"""
inspect_dataset.py

Run this on any downloaded dataset BEFORE converting it. It reports:
  - folder layout and file counts by extension
  - which annotation formats it found (COCO JSON, Pascal VOC XML,
    YOLO TXT, CSV, or mask images)
  - the class names and how many boxes each has

Paste the output back so the class mapping for convert_to_yolo.py
can be decided from facts, not guesses.

Usage:
  python inspect_dataset.py /kaggle/input/signverod
"""

import csv
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
CSV_BOX_COLS = {"xmin", "ymin", "xmax", "ymax"}


def tree(root, max_dirs=40):
    print("Folder layout (directories with file counts):")
    shown = 0
    for d in sorted([root] + [p for p in root.rglob("*") if p.is_dir()]):
        files = [f for f in d.iterdir() if f.is_file()]
        if not files:
            continue
        exts = Counter(f.suffix.lower() or "(none)" for f in files)
        rel = d.relative_to(root).as_posix() or "."
        print(f"  {rel}/  " + ", ".join(f"{e}:{n}" for e, n in exts.most_common(5)))
        shown += 1
        if shown >= max_dirs:
            print("  ... (more directories not shown)")
            break


def check_coco(files):
    found = False
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not (isinstance(data, dict) and {"images", "annotations", "categories"} <= data.keys()):
            continue
        found = True
        cats = {c["id"]: c["name"] for c in data["categories"]}
        counts = Counter(cats.get(a["category_id"], "?") for a in data["annotations"])
        print(f"\n[COCO JSON] {f}")
        print(f"  images: {len(data['images'])}, boxes: {len(data['annotations'])}")
        for name, n in counts.most_common():
            print(f"  class '{name}': {n} boxes")
    return found


def check_voc(files):
    counts, n_files = Counter(), 0
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except Exception:
            continue
        if root.tag != "annotation":
            continue
        n_files += 1
        for obj in root.iter("object"):
            name = obj.findtext("name", default="?").strip()
            counts[name] += 1
    if n_files:
        print(f"\n[Pascal VOC XML] {n_files} annotation files")
        for name, n in counts.most_common():
            print(f"  class '{name}': {n} boxes")
    return n_files > 0


def check_yolo(root, txt_files):
    counts, n_files = Counter(), 0
    for f in txt_files:
        lines = [l.split() for l in f.read_text(encoding="utf-8", errors="ignore").splitlines() if l.strip()]
        if not lines or not all(len(l) == 5 and all(_is_number(v) for v in l) for l in lines):
            continue
        n_files += 1
        for l in lines:
            counts[int(float(l[0]))] += 1
    if not n_files:
        return False
    names = find_yolo_names(root)
    print(f"\n[YOLO TXT] {n_files} label files")
    print(f"  class names file: {names[1] if names else 'NOT FOUND'}")
    for cid, n in sorted(counts.items()):
        label = names[0][cid] if names and cid < len(names[0]) else "?"
        print(f"  class id {cid} ('{label}'): {n} boxes")
    return True


def find_yolo_names(root):
    for f in list(root.rglob("classes.txt")) + list(root.rglob("*.names")):
        return [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()], f
    for f in list(root.rglob("data.yaml")) + list(root.rglob("*.yaml")):
        names = parse_yaml_names(f)
        if names:
            return names, f
    return None


def parse_yaml_names(f):
    """Read 'names' from a YOLO data.yaml without needing PyYAML."""
    try:
        import yaml
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        names = data.get("names") if isinstance(data, dict) else None
        if isinstance(names, dict):
            return [names[k] for k in sorted(names)]
        if isinstance(names, list):
            return names
    except Exception:
        pass
    return None


def check_csv(files):
    found = False
    for f in files:
        try:
            with open(f, newline="", encoding="utf-8", errors="ignore") as fh:
                reader = csv.DictReader(fh)
                cols = {c.strip().lower() for c in (reader.fieldnames or [])}
                if not CSV_BOX_COLS <= cols:
                    continue
                rows = list(reader)
        except Exception:
            continue
        found = True
        class_col = next((c for c in (reader.fieldnames or []) if c.strip().lower() in ("class", "label", "name")), None)
        counts = Counter(r[class_col] for r in rows) if class_col else Counter({"(no class column)": len(rows)})
        print(f"\n[CSV boxes] {f}  columns: {reader.fieldnames}")
        for name, n in counts.most_common():
            print(f"  class '{name}': {n} boxes")
    return found


def check_masks(root):
    mask_dirs = [d for d in root.rglob("*") if d.is_dir()
                 and any(k in d.name.lower() for k in ("mask", "gt", "ground", "truth"))]
    for d in mask_dirs:
        imgs = [f for f in d.iterdir() if f.suffix.lower() in IMG_EXTS]
        if imgs:
            print(f"\n[Possible mask folder] {d}  ({len(imgs)} images)  example: {imgs[0].name}")
    return bool(mask_dirs)


def _is_number(v):
    try:
        float(v)
        return True
    except ValueError:
        return False


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python inspect_dataset.py <dataset_folder>")
    root = Path(sys.argv[1])
    if not root.is_dir():
        sys.exit(f"Not a folder: {root}")

    all_files = [p for p in root.rglob("*") if p.is_file()]
    images = [p for p in all_files if p.suffix.lower() in IMG_EXTS]
    print(f"Dataset: {root}")
    print(f"Total files: {len(all_files)}, images: {len(images)}\n")
    tree(root)

    by_ext = lambda e: [p for p in all_files if p.suffix.lower() == e]
    found = [
        check_coco(by_ext(".json")),
        check_voc(by_ext(".xml")),
        check_yolo(root, by_ext(".txt")),
        check_csv(by_ext(".csv")),
        check_masks(root),
    ]
    if not any(found):
        print("\nNo bounding-box annotations found. This dataset cannot be used "
              "for detection without annotating it yourself.")


if __name__ == "__main__":
    main()
