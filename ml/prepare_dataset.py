"""
prepare_dataset.py

Merges one or more annotated folders (images + YOLO labels + classes.txt)
into a clean YOLO dataset with train / val / test splits.

Every source folder must contain images, labels and classes.txt. That is what
Label Studio's YOLO export, convert_to_yolo.py and the synthetic export give.

What it does:
  1. Remaps class ids BY NAME to the canonical order, per source.
  2. Validates every label line (5 values, known class, coords in 0..1).
  3. Applies EXIF rotation and strips EXIF metadata (removes phone GPS data).
  4. Removes exact duplicate images across all sources.
  5. Splits by GROUP: photos named certXYZ__anything share group certXYZ and
     always land in the same split, so test images are truly unseen.
  6. --test-from: the test split is drawn ONLY from these folders (your own
     real Indian certificates). Other sources (Kaggle) go to train/val only,
     so the reported score measures the target domain.
  7. --synthetic: added to TRAIN only.

Usage:
  python prepare_dataset.py --src conv/signverod conv/stamps ../exports/real \
      --out ../datasets/mota_mix

  python prepare_dataset.py --src conv/signverod conv/stamps \
      --test-from ../exports/real --synthetic ../exports/synthetic \
      --out ../datasets/mota_mix
"""

import argparse
import hashlib
import random
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageOps

CLASSES = ["official_seal", "tehsildar_sign", "income_box", "st_box", "qr_code"]
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MIN_TRAIN_INSTANCES = 50


def find_dirs(src):
    if (src / "images").is_dir() and (src / "labels").is_dir():
        return src / "images", src / "labels"
    return src, src


def read_source_classes(src, labels_dir):
    for candidate in (src / "classes.txt", labels_dir / "classes.txt"):
        if candidate.is_file():
            names = [n.strip() for n in candidate.read_text(encoding="utf-8").splitlines() if n.strip()]
            unknown = [n for n in names if n not in CLASSES]
            if unknown:
                sys.exit(f"ERROR: {candidate} has unknown class names: {unknown}. Allowed: {CLASSES}")
            return names
    sys.exit(f"ERROR: classes.txt not found in {src}")


def parse_label_file(path, id_map):
    lines, errors = [], []
    if not path.is_file():
        return None, [f"{path.name}: missing label file"]
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        parts = raw.split()
        if not parts:
            continue
        if len(parts) != 5:
            errors.append(f"{path.name} line {n}: expected 5 values, got {len(parts)}")
            continue
        try:
            src_id = int(parts[0])
            x, y, w, h = (float(v) for v in parts[1:])
        except ValueError:
            errors.append(f"{path.name} line {n}: non-numeric value")
            continue
        if src_id not in id_map:
            errors.append(f"{path.name} line {n}: class id {src_id} not in classes.txt")
            continue
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
            errors.append(f"{path.name} line {n}: coordinates out of range")
            continue
        lines.append(f"{id_map[src_id]} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
    return lines, errors


def collect(src, allow_empty, seen_hashes):
    """Return list of (image_path, label_lines) from one folder."""
    src = Path(src)
    images_dir, labels_dir = find_dirs(src)
    names = read_source_classes(src, labels_dir)
    id_map = {i: CLASSES.index(name) for i, name in enumerate(names)}

    items, errors, dupes = [], [], 0
    for img in sorted(images_dir.iterdir()):
        if img.suffix.lower() not in IMG_EXTS:
            continue
        digest = hashlib.md5(img.read_bytes()).hexdigest()
        if digest in seen_hashes:
            dupes += 1
            continue
        seen_hashes.add(digest)
        lines, errs = parse_label_file(labels_dir / f"{img.stem}.txt", id_map)
        if lines is None:
            if not allow_empty:
                errors.extend(errs)
                continue
            lines, errs = [], []
        errors.extend(errs)
        if not lines and not allow_empty:
            errors.append(f"{img.name}: no boxes (use --allow-empty for background images)")
            continue
        items.append((img, lines))
    print(f"  {src}: {len(items)} images accepted, {dupes} duplicates removed, {len(errors)} problems")
    return items, errors


def group_key(path):
    return path.stem.split("__")[0]


def split_groups(items, val_frac, test_frac, seed):
    groups = defaultdict(list)
    for item in items:
        groups[group_key(item[0])].append(item)
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    n = len(keys)
    n_test = round(n * test_frac) if test_frac > 0 else 0
    n_val = max(1, round(n * val_frac))
    if test_frac > 0:
        n_test = max(1, n_test)
    if n_test + n_val >= n:
        sys.exit(f"ERROR: only {n} image groups; need more data to split.")
    pick = lambda ks: [it for k in ks for it in groups[k]]
    return (pick(keys[n_test + n_val:]), pick(keys[n_test:n_test + n_val]),
            pick(keys[:n_test]), n)


def write_split(items, out, split, used_names, prefix=""):
    img_dir, lbl_dir = out / "images" / split, out / "labels" / split
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    for img_path, lines in items:
        name, i = f"{prefix}{img_path.stem}", 1
        base = name
        while name in used_names:
            name, i = f"{base}-{i}", i + 1
        used_names.add(name)
        with Image.open(img_path) as im:
            ImageOps.exif_transpose(im).convert("RGB").save(img_dir / f"{name}.jpg", quality=95)
        (lbl_dir / f"{name}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        for line in lines:
            counts[CLASSES[int(line.split()[0])]] += 1
    return counts


def main():
    ap = argparse.ArgumentParser(description="Prepare MoTA-SANKALP YOLO dataset")
    ap.add_argument("--src", nargs="+", required=True, help="One or more annotated folders")
    ap.add_argument("--test-from", nargs="*", default=[],
                    help="Folders the test split is drawn from (your own certificates)")
    ap.add_argument("--synthetic", help="Synthetic folder (train only)")
    ap.add_argument("--synthetic-ratio", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--test", type=float, default=0.15, help="Test fraction of image groups")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--allow-empty", action="store_true")
    ap.add_argument("--strict", action="store_true", help="Stop on any annotation problem")
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    seen, errors = set(), []

    print("Reading sources:")
    main_items = []
    for s in args.src:
        items, errs = collect(s, args.allow_empty, seen)
        main_items += items
        errors += errs
    target_items = []
    for s in args.test_from:
        items, errs = collect(s, args.allow_empty, seen)
        target_items += items
        errors += errs

    if errors:
        print(f"\nAnnotation problems ({len(errors)}):")
        for e in errors[:50]:
            print("  " + e)
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        if args.strict:
            sys.exit("Stopping because --strict is set.")

    if target_items:
        # Test comes only from the target-domain folders; other sources: train/val
        t_train, t_val, test, t_groups = split_groups(target_items, args.val, args.test, args.seed)
        o_train, o_val, _, o_groups = split_groups(main_items, args.val, 0.0, args.seed)
        train, val = t_train + o_train, t_val + o_val
        print(f"\nImage groups: {t_groups} in --test-from, {o_groups} in --src")
    else:
        train, val, test, n_groups = split_groups(main_items, args.val, args.test, args.seed)
        print(f"\nImage groups in --src: {n_groups}")

    used = set()
    report = {"train": write_split(train, out, "train", used),
              "val": write_split(val, out, "val", used),
              "test": write_split(test, out, "test", used)}
    sizes = {"train": len(train), "val": len(val), "test": len(test)}

    if args.synthetic:
        synth, s_errs = collect(args.synthetic, args.allow_empty, seen)
        random.Random(args.seed).shuffle(synth)
        synth = synth[: int(len(train) * args.synthetic_ratio)]
        report["train"] += write_split(synth, out, "train", used, prefix="syn_")
        sizes["train"] += len(synth)
        print(f"Synthetic images added to train only: {len(synth)}")

    (out / "data.yaml").write_text(
        f"path: {out.resolve().as_posix()}\n"
        "train: images/train\nval: images/val\ntest: images/test\n"
        f"nc: {len(CLASSES)}\nnames: {CLASSES}\n", encoding="utf-8")

    print("\nImages per split: " + ", ".join(f"{k}={v}" for k, v in sizes.items()))
    if target_items:
        print("Test split contains ONLY images from --test-from folders")
    print(f"\n{'class':<16}{'train':>8}{'val':>8}{'test':>8}")
    weak = []
    for c in CLASSES:
        tr, va, te = report["train"][c], report["val"][c], report["test"][c]
        print(f"{c:<16}{tr:>8}{va:>8}{te:>8}")
        if tr < MIN_TRAIN_INSTANCES or te == 0:
            weak.append(c)
    if weak:
        print(f"\nWARNING: too little data for {weak} (want >= {MIN_TRAIN_INSTANCES} train "
              "boxes and at least 1 test box). Metrics for these classes will be unreliable.")
    print(f"\nWrote {out / 'data.yaml'}")


if __name__ == "__main__":
    main()
