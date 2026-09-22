"""
convert_to_yolo.py

Converts a downloaded detection dataset into the MoTA-SANKALP layout:
    <out>/images/*.jpg
    <out>/labels/*.txt       (YOLO format, canonical class ids)
    <out>/classes.txt        (the 5 canonical names)

The output folder can go straight into prepare_dataset.py --src.

Supported input formats (auto-detected, or force with --format):
    coco   JSON with images / annotations / categories
    voc    Pascal VOC XML files
    yolo   YOLO .txt labels + classes.txt or data.yaml
    csv    CSV with filename, class, xmin, ymin, xmax, ymax columns
    masks  binary mask images (needs --images and --masks)

Source classes are mapped BY NAME with --map. Classes you do not map are
dropped. Run inspect_dataset.py first to see the exact source class names.

Examples:
  python convert_to_yolo.py --src /kaggle/input/signverod --out conv/signverod \
      --prefix sv --map signature=tehsildar_sign

  python convert_to_yolo.py --src /kaggle/input/stamp-data --out conv/stamps \
      --prefix st --map stamp=official_seal

  python convert_to_yolo.py --format masks --images data/scans --masks data/gt \
      --out conv/staver --prefix sv2 --mask-class official_seal
"""

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

CLASSES = ["official_seal", "tehsildar_sign", "income_box", "st_box", "qr_code"]
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
MASK_SUFFIXES = ("_gt", "-gt", "_mask", "-mask", "_label", "_GT")


class Collector:
    """Holds boxes per image in pixel coordinates of the declared image size."""

    def __init__(self, mapping):
        self.mapping = mapping
        self.boxes = defaultdict(list)       # image path -> [(cls, x1, y1, x2, y2)]
        self.declared = {}                   # image path -> (w, h) from annotation
        self.dropped = Counter()
        self.missing_images = set()

    def add(self, img_path, src_name, x1, y1, x2, y2, declared=None):
        if img_path is None:
            return
        key = self.mapping.get(str(src_name).strip().lower())
        if key is None:
            self.dropped[str(src_name)] += 1
            self.boxes.setdefault(img_path, [])
            return
        self.boxes[img_path].append((CLASSES.index(key), x1, y1, x2, y2))
        if declared and all(declared):
            self.declared[img_path] = declared

    def touch(self, img_path):
        if img_path is not None:
            self.boxes.setdefault(img_path, [])


def build_index(root):
    by_name, by_stem = {}, defaultdict(list)
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            by_name.setdefault(p.name, p)
            by_stem[p.stem].append(p)
    return by_name, by_stem


def resolve(candidates, name, by_name, by_stem, col):
    for c in candidates:
        if c.is_file():
            return c
    base = Path(name).name
    if base in by_name:
        return by_name[base]
    hits = by_stem.get(Path(name).stem, [])
    if len(hits) == 1:
        return hits[0]
    col.missing_images.add(name)
    return None


# ---------------- readers ----------------

def read_coco(root, col, by_name, by_stem):
    n = 0
    for jf in root.rglob("*.json"):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not (isinstance(data, dict) and {"images", "annotations", "categories"} <= data.keys()):
            continue
        n += 1
        cats = {c["id"]: c["name"] for c in data["categories"]}
        images = {}
        for im in data["images"]:
            fn = im["file_name"]
            path = resolve([jf.parent / fn, jf.parent / "images" / fn, root / fn],
                           fn, by_name, by_stem, col)
            images[im["id"]] = (path, (im.get("width"), im.get("height")))
            col.touch(path)
        for a in data["annotations"]:
            if a["image_id"] not in images or "bbox" not in a:
                continue
            path, dims = images[a["image_id"]]
            x, y, w, h = a["bbox"]
            col.add(path, cats.get(a["category_id"], "?"), x, y, x + w, y + h, dims)
    return n


def read_voc(root, col, by_name, by_stem):
    n = 0
    for xf in root.rglob("*.xml"):
        try:
            ann = ET.parse(xf).getroot()
        except Exception:
            continue
        if ann.tag != "annotation":
            continue
        n += 1
        fn = ann.findtext("filename") or xf.stem
        cands = [xf.parent / fn, xf.parent.parent / "images" / fn,
                 xf.parent.parent / "JPEGImages" / fn]
        cands += [xf.with_suffix(e) for e in IMG_EXTS]
        path = resolve(cands, fn, by_name, by_stem, col)
        size = ann.find("size")
        dims = (int(float(size.findtext("width", "0"))), int(float(size.findtext("height", "0")))) if size is not None else None
        col.touch(path)
        for obj in ann.iter("object"):
            bb = obj.find("bndbox")
            if bb is None:
                continue
            vals = [float(bb.findtext(k, "0")) for k in ("xmin", "ymin", "xmax", "ymax")]
            col.add(path, obj.findtext("name", "?"), *vals, dims)
    return n


def yolo_names(root):
    for f in list(root.rglob("classes.txt")) + list(root.rglob("*.names")):
        return [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    try:
        import yaml
    except ImportError:
        return None
    for f in list(root.rglob("data.yaml")) + list(root.rglob("*.yaml")):
        try:
            names = yaml.safe_load(f.read_text(encoding="utf-8")).get("names")
        except Exception:
            continue
        if isinstance(names, dict):
            return [names[k] for k in sorted(names)]
        if isinstance(names, list):
            return names
    return None


def read_yolo(root, col, by_name, by_stem):
    names = yolo_names(root)
    if not names:
        return 0
    n = 0
    for tf in root.rglob("*.txt"):
        rows = [l.split() for l in tf.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()]
        try:
            rows = [[float(v) for v in r] for r in rows]
        except ValueError:
            continue
        if not all(len(r) == 5 for r in rows):
            continue
        img_dir = Path(str(tf.parent).replace("labels", "images"))
        cands = [img_dir / (tf.stem + e) for e in IMG_EXTS] + [tf.with_suffix(e) for e in IMG_EXTS]
        path = next((c for c in cands if c.is_file()), None)
        if path is None:
            hits = by_stem.get(tf.stem, [])
            path = hits[0] if len(hits) == 1 else None
        if path is None:
            if tf.name != "classes.txt":
                col.missing_images.add(tf.name)
            continue
        n += 1
        col.touch(path)
        with Image.open(path) as im:
            w, h = im.size
        for c, xc, yc, bw, bh in rows:
            name = names[int(c)] if int(c) < len(names) else "?"
            col.add(path, name, (xc - bw / 2) * w, (yc - bh / 2) * h,
                    (xc + bw / 2) * w, (yc + bh / 2) * h, (w, h))
    return n


def read_csv(root, col, by_name, by_stem, default_class):
    n = 0
    for cf in root.rglob("*.csv"):
        with open(cf, newline="", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            cols = {c.strip().lower(): c for c in (reader.fieldnames or [])}
            if not {"xmin", "ymin", "xmax", "ymax"} <= cols.keys():
                continue
            file_col = next((cols[k] for k in ("filename", "file", "image", "image_id", "path", "file_name") if k in cols), None)
            class_col = next((cols[k] for k in ("class", "label", "name", "category") if k in cols), None)
            if file_col is None:
                continue
            n += 1
            for r in reader:
                fn = r[file_col].strip()
                path = resolve([cf.parent / fn, root / fn], fn, by_name, by_stem, col)
                dims = None
                if "width" in cols and "height" in cols:
                    try:
                        dims = (int(float(r[cols["width"]])), int(float(r[cols["height"]])))
                    except ValueError:
                        dims = None
                name = r[class_col] if class_col else default_class
                vals = [float(r[cols[k]]) for k in ("xmin", "ymin", "xmax", "ymax")]
                col.add(path, name, *vals, dims)
    return n


def read_masks(images_dir, masks_dir, col, mask_class, min_area_frac, dilate):
    by_stem = {}
    for p in images_dir.rglob("*"):
        if p.suffix.lower() in IMG_EXTS:
            by_stem[p.stem] = p
    n = 0
    for mp in masks_dir.rglob("*"):
        if mp.suffix.lower() not in IMG_EXTS:
            continue
        stem = mp.stem
        for s in MASK_SUFFIXES:
            if stem.endswith(s):
                stem = stem[: -len(s)]
        img = by_stem.get(stem)
        if img is None:
            col.missing_images.add(mp.name)
            continue
        mask = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE)
        if mask is None:
            continue
        n += 1
        col.touch(img)
        binary = (mask > 127).astype(np.uint8)
        grouped = cv2.dilate(binary, np.ones((dilate, dilate), np.uint8))
        count, labels = cv2.connectedComponents(grouped)
        h, w = binary.shape
        for k in range(1, count):
            ys, xs = np.nonzero((labels == k) & (binary == 1))
            if len(xs) == 0:
                continue
            x1, y1, x2, y2 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
            if (x2 - x1) * (y2 - y1) < min_area_frac * w * h:
                continue
            col.add(img, mask_class, x1, y1, x2, y2, (w, h))
    return n


# ---------------- writer ----------------

def write_output(col, out, prefix, max_side, keep_empty, limit):
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "labels").mkdir(parents=True, exist_ok=True)
    (out / "classes.txt").write_text("\n".join(CLASSES) + "\n", encoding="utf-8")

    counts, written, empty_skipped, tiny = Counter(), 0, 0, 0
    used = set()
    for img_path in sorted(col.boxes):
        boxes = col.boxes[img_path]
        if not boxes and not keep_empty:
            empty_skipped += 1
            continue
        if limit and written >= limit:
            break
        try:
            with Image.open(img_path) as im:
                im = im.convert("RGB")
                aw, ah = im.size
                scale = min(1.0, max_side / max(aw, ah))
                if scale < 1.0:
                    im = im.resize((round(aw * scale), round(ah * scale)))
                name = f"{prefix}-{img_path.stem}".replace("__", "_").replace(" ", "_")
                base, i = name, 1
                while name in used:
                    name, i = f"{base}-{i}", i + 1
                used.add(name)
                im.save(out / "images" / f"{name}.jpg", quality=92)
        except Exception as exc:
            print(f"  skipped unreadable image {img_path}: {exc}")
            continue

        dw, dh = col.declared.get(img_path, (aw, ah))
        lines = []
        for c, x1, y1, x2, y2 in boxes:
            x1, x2 = sorted((max(0.0, x1), min(float(dw), x2)))
            y1, y2 = sorted((max(0.0, y1), min(float(dh), y2)))
            if (x2 - x1) < 2 or (y2 - y1) < 2:
                tiny += 1
                continue
            lines.append(f"{c} {(x1 + x2) / 2 / dw:.6f} {(y1 + y2) / 2 / dh:.6f} "
                         f"{(x2 - x1) / dw:.6f} {(y2 - y1) / dh:.6f}")
            counts[CLASSES[c]] += 1
        (out / "labels" / f"{name}.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        written += 1
    return counts, written, empty_skipped, tiny


def parse_map(items):
    mapping = {}
    for item in items or []:
        if "=" not in item:
            sys.exit(f"ERROR: --map expects source=target, got '{item}'")
        src, dst = (s.strip() for s in item.split("=", 1))
        if dst not in CLASSES:
            sys.exit(f"ERROR: target '{dst}' is not one of {CLASSES}")
        mapping[src.lower()] = dst
    return mapping


def main():
    ap = argparse.ArgumentParser(description="Convert a detection dataset to MoTA-SANKALP YOLO layout")
    ap.add_argument("--src", help="Dataset root (for coco/voc/yolo/csv)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", required=True, help="Short tag for output file names, e.g. sv")
    ap.add_argument("--format", default="auto", choices=["auto", "coco", "voc", "yolo", "csv", "masks"])
    ap.add_argument("--map", nargs="*", help="source_class=target_class (repeatable)")
    ap.add_argument("--csv-class", default="object", help="Class name when a CSV has no class column")
    ap.add_argument("--images", help="Masks mode: folder of document images")
    ap.add_argument("--masks", help="Masks mode: folder of binary mask images")
    ap.add_argument("--mask-class", default="official_seal", choices=CLASSES)
    ap.add_argument("--mask-min-area", type=float, default=0.0005, help="Min box area as fraction of image")
    ap.add_argument("--mask-dilate", type=int, default=25, help="Pixels used to merge mask fragments")
    ap.add_argument("--max-side", type=int, default=1600, help="Downscale images so longest side <= this")
    ap.add_argument("--keep-empty", action="store_true", help="Keep images with no mapped boxes")
    ap.add_argument("--limit", type=int, default=0, help="Max images to write (0 = all)")
    args = ap.parse_args()

    out = Path(args.out)
    if args.format == "masks":
        if not (args.images and args.masks):
            sys.exit("ERROR: masks format needs --images and --masks")
        col = Collector({args.mask_class: args.mask_class})
        n = read_masks(Path(args.images), Path(args.masks), col, args.mask_class,
                       args.mask_min_area, args.mask_dilate)
        used_format = "masks"
    else:
        if not args.src:
            sys.exit("ERROR: --src is required")
        mapping = parse_map(args.map)
        if not mapping:
            sys.exit("ERROR: give at least one --map source=target. "
                     "Run inspect_dataset.py to see the source class names.")
        root = Path(args.src)
        by_name, by_stem = build_index(root)
        col = Collector(mapping)
        readers = {
            "coco": lambda: read_coco(root, col, by_name, by_stem),
            "voc": lambda: read_voc(root, col, by_name, by_stem),
            "yolo": lambda: read_yolo(root, col, by_name, by_stem),
            "csv": lambda: read_csv(root, col, by_name, by_stem, args.csv_class),
        }
        order = [args.format] if args.format != "auto" else ["coco", "voc", "yolo", "csv"]
        n, used_format = 0, None
        for fmt in order:
            n = readers[fmt]()
            if n:
                used_format = fmt
                break
        if not n:
            sys.exit("ERROR: no supported annotations found. Run inspect_dataset.py on this folder.")

    counts, written, empty_skipped, tiny = write_output(
        col, out, args.prefix, args.max_side, args.keep_empty, args.limit)

    print(f"Format used: {used_format} ({n} annotation sources)")
    print(f"Images written: {written}   skipped with no mapped boxes: {empty_skipped}")
    for c in CLASSES:
        if counts[c]:
            print(f"  {c}: {counts[c]} boxes")
    if col.dropped:
        print("Dropped source classes (not mapped): " +
              ", ".join(f"{k}={v}" for k, v in col.dropped.most_common()))
    if tiny:
        print(f"Boxes discarded as too small or invalid: {tiny}")
    if col.missing_images:
        ex = sorted(col.missing_images)[:5]
        print(f"WARNING: {len(col.missing_images)} annotations point to images not found, e.g. {ex}")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
