"""Convert, remap and merge the downloaded datasets into one YOLO dataset.

Auto-detects each source's annotation format: YOLO txt, Pascal VOC xml, or COCO json.

python training/yolo/prepare_dataset.py --inspect              # show formats + class names per source
python training/yolo/prepare_dataset.py --stage base           # public data only  -> dataset_base.yaml
python training/yolo/prepare_dataset.py --stage finetune       # public + own      -> dataset_finetune.yaml
"""
import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import yaml
from PIL import Image

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


# ------------------------------------------------------------------ readers
# every reader returns a list of (image_path, [(class_name, cx, cy, w, h), ...]) in normalised coords

def _names_from_yaml(root: Path):
    for y in list(root.rglob("*.yaml")) + list(root.rglob("*.yml")):
        try:
            data = yaml.safe_load(open(y, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "names" in data:
            names = data["names"]
            return {int(k): str(v) for k, v in names.items()} if isinstance(names, dict) else dict(enumerate(map(str, names)))
    for c in list(root.rglob("classes.txt")) + list(root.rglob("obj.names")):
        lines = [l.strip() for l in open(c, encoding="utf-8") if l.strip()]
        return dict(enumerate(lines))
    return {}


def _label_for(img: Path) -> Path | None:
    same = img.with_suffix(".txt")
    if same.exists():
        return same
    parts = list(img.parts)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i] == "images":
            cand = Path(*parts[:i], "labels", *parts[i + 1:]).with_suffix(".txt")
            if cand.exists():
                return cand
    return None


def read_yolo(root: Path):
    names = _names_from_yaml(root)
    items = []
    for img in root.rglob("*"):
        if img.suffix.lower() not in IMG_EXT:
            continue
        lbl = _label_for(img)
        if lbl is None:
            continue
        boxes = []
        for line in open(lbl, encoding="utf-8", errors="ignore"):
            p = line.split()
            if len(p) < 5:
                continue
            cid = int(float(p[0]))
            vals = list(map(float, p[1:]))
            if len(vals) > 4:  # polygon / segmentation row -> bounding box
                xs, ys = vals[0::2], vals[1::2]
                x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
                vals = [(x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0]
            boxes.append((names.get(cid, str(cid)), *vals[:4]))
        items.append((img, boxes))
    return items


def read_voc(root: Path):
    index = {p.stem: p for p in root.rglob("*") if p.suffix.lower() in IMG_EXT}
    items = []
    for x in root.rglob("*.xml"):
        try:
            tree = ET.parse(x).getroot()
        except ET.ParseError:
            continue
        if tree.find("object") is None and tree.find("size") is None:
            continue
        fname = (tree.findtext("filename") or "").strip()
        img = index.get(Path(fname).stem) or index.get(x.stem)
        if img is None:
            continue
        size = tree.find("size")
        if size is not None and size.findtext("width"):
            W, H = float(size.findtext("width")), float(size.findtext("height"))
        else:
            with Image.open(img) as im:
                W, H = im.size
        if W <= 0 or H <= 0:
            with Image.open(img) as im:
                W, H = im.size
        boxes = []
        for obj in tree.findall("object"):
            bb = obj.find("bndbox")
            if bb is None:
                continue
            x0, y0, x1, y1 = (float(bb.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax"))
            boxes.append((obj.findtext("name").strip(), (x0 + x1) / 2 / W, (y0 + y1) / 2 / H, (x1 - x0) / W, (y1 - y0) / H))
        items.append((img, boxes))
    return items


def read_coco(root: Path):
    items = []
    index = {p.name: p for p in root.rglob("*") if p.suffix.lower() in IMG_EXT}
    for j in root.rglob("*.json"):
        try:
            data = json.load(open(j, encoding="utf-8"))
        except Exception:
            continue
        if not (isinstance(data, dict) and {"images", "annotations", "categories"} <= data.keys()):
            continue
        cats = {c["id"]: c["name"] for c in data["categories"]}
        imgs = {i["id"]: i for i in data["images"]}
        per = {}
        for a in data["annotations"]:
            im = imgs.get(a["image_id"])
            if not im or "bbox" not in a:
                continue
            x, y, w, h = a["bbox"]
            W, H = im["width"], im["height"]
            per.setdefault(a["image_id"], []).append((cats[a["category_id"]], (x + w / 2) / W, (y + h / 2) / H, w / W, h / H))
        for iid, im in imgs.items():
            path = index.get(Path(im["file_name"]).name)
            if path:
                items.append((path, per.get(iid, [])))
    return items


def detect_and_read(root: Path):
    counts = {}
    for fmt, reader in (("coco", read_coco), ("voc", read_voc), ("yolo", read_yolo)):
        items = reader(root)
        n_boxes = sum(len(b) for _, b in items)
        counts[fmt] = (n_boxes, items)
    fmt = max(counts, key=lambda k: counts[k][0])
    return fmt, counts[fmt][1]


# ------------------------------------------------------------------ mapping

def build_mapper(class_map, targets):
    if class_map == "identity":
        return lambda name: name if name in targets else None
    cmap = {str(k).lower(): v for k, v in (class_map or {}).items()}

    def m(name):
        n = str(name).lower()
        if n in cmap:
            return cmap[n]
        return cmap.get("*")
    return m


def split_of(key: str) -> str:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16) % 100
    return "train" if h < 70 else ("val" if h < 85 else "test")


def clamp_box(cx, cy, w, h):
    x0, y0 = max(0.0, cx - w / 2), max(0.0, cy - h / 2)
    x1, y1 = min(1.0, cx + w / 2), min(1.0, cy + h / 2)
    if x1 - x0 <= 0.001 or y1 - y0 <= 0.001:
        return None
    return (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0


# ------------------------------------------------------------------ main

def source_root(src):
    return (HERE / src["path"]) if src["type"] == "local" else RAW / src["key"]


def inspect(cfg):
    for src in cfg["sources"]:
        if src.get("enabled", True) is False:
            continue
        root = source_root(src)
        print(f"\n[{src['key']}] {root}")
        if not root.exists():
            print("  not downloaded / not found")
            continue
        fmt, items = detect_and_read(root)
        names = Counter(n for _, boxes in items for n, *_ in boxes)
        mapper = build_mapper(src.get("class_map"), cfg["target_classes"])
        print(f"  format={fmt}  images_with_labels={len(items)}  boxes={sum(names.values())}")
        for n, c in names.most_common():
            print(f"    {n!r:30} x{c:<6} -> {mapper(n) or 'DROPPED'}")


def build(cfg, stage: str, background_ratio: float):
    targets = cfg["target_classes"]
    tid = {n: i for i, n in enumerate(targets)}
    out = HERE / "datasets" / f"mota_real_{stage}"
    if out.exists():
        shutil.rmtree(out)
    for s in ("train", "val", "test"):
        (out / "images" / s).mkdir(parents=True)
        (out / "labels" / s).mkdir(parents=True)

    totals = Counter()
    split_counts = Counter()
    for src in cfg["sources"]:
        if src.get("enabled", True) is False or stage not in src.get("stages", ["base", "finetune"]):
            continue
        root = source_root(src)
        if not root.exists():
            print(f"[{src['key']}] skipped (not found at {root})")
            continue
        fmt, items = detect_and_read(root)
        mapper = build_mapper(src.get("class_map"), targets)
        repeat = int(src.get("repeat", 1))
        kept = bg = 0
        for img, boxes in items:
            lines = []
            for name, cx, cy, w, h in boxes:
                t = mapper(name)
                if t is None:
                    continue
                b = clamp_box(cx, cy, w, h)
                if b:
                    lines.append(f"{tid[t]} {b[0]:.6f} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f}")
                    totals[t] += 1
            if not lines:
                # keep a limited number of images with no target objects as negatives
                if bg >= background_ratio * max(kept, 1):
                    continue
                bg += 1
            else:
                kept += 1
            base_name = f"{src['key']}__{hashlib.md5(str(img).encode()).hexdigest()[:10]}"
            split = split_of(base_name)
            copies = repeat if split == "train" else 1
            for r in range(copies):
                name = base_name + (f"_r{r}" if r else "")
                shutil.copy2(img, out / "images" / split / (name + img.suffix.lower()))
                (out / "labels" / split / (name + ".txt")).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="ascii")
                split_counts[split] += 1
        print(f"[{src['key']}] format={fmt} kept={kept} negatives={bg} repeat={repeat}")

    yaml_path = HERE / f"dataset_{stage}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump({"path": str(out.resolve()).replace("\\", "/"), "train": "images/train", "val": "images/val",
                        "test": "images/test", "names": dict(enumerate(targets))}, f, sort_keys=False)
    print(f"\nImages per split: {dict(split_counts)}")
    print("Boxes per class:")
    for t in targets:
        warn = "   <-- no data: add your own annotated certificates" if totals[t] == 0 else ""
        print(f"  {t:22} {totals[t]}{warn}")
    print(f"\nWrote {yaml_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--stage", choices=["base", "finetune"], default="base")
    ap.add_argument("--background-ratio", type=float, default=0.1, help="max negatives per positive image")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(HERE / "sources.yaml", encoding="utf-8"))
    if args.inspect:
        inspect(cfg)
    else:
        build(cfg, args.stage, args.background_ratio)


if __name__ == "__main__":
    main()
