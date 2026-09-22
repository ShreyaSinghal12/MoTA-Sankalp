"""
autolabel_qr.py

Adds qr_code boxes to a dataset folder (images/, labels/, classes.txt)
using OpenCV's QR detector. No public QR detection dataset is needed:
QR codes on certificates are found reliably by OpenCV itself.

Existing labels are kept. A QR box is added only if it does not overlap an
existing qr_code box. Review a sample of the results in Label Studio before
training, because OpenCV can miss damaged or very small codes.

Usage:
  python autolabel_qr.py --dir ../exports/real
  python autolabel_qr.py --dir conv/signverod --dry-run
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
QR_NAME = "qr_code"


def find_qr_boxes(image):
    """Return QR boxes as (x1, y1, x2, y2) in pixels. Tries a few preprocessings."""
    detector = cv2.QRCodeDetector()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    attempts = [(image, 1.0), (gray, 1.0)]
    if max(gray.shape) < 1600:
        attempts.append((cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC), 2.0))
    for img, scale in attempts:
        ok, points = detector.detectMulti(img)
        if ok and points is not None and len(points):
            boxes = []
            for quad in points:
                quad = np.asarray(quad) / scale
                x1, y1 = quad.min(axis=0)
                x2, y2 = quad.max(axis=0)
                pad = 0.04 * max(x2 - x1, y2 - y1)   # include the quiet zone edge
                boxes.append((x1 - pad, y1 - pad, x2 + pad, y2 + pad))
            return boxes
    return []


def iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def main():
    ap = argparse.ArgumentParser(description="Auto-label QR codes with OpenCV")
    ap.add_argument("--dir", required=True, help="Folder with images/, labels/, classes.txt")
    ap.add_argument("--dry-run", action="store_true", help="Only count, do not write")
    args = ap.parse_args()

    root = Path(args.dir)
    images_dir, labels_dir = root / "images", root / "labels"
    classes_file = root / "classes.txt"
    names = [l.strip() for l in classes_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    if QR_NAME not in names:
        names.append(QR_NAME)
        if not args.dry_run:
            classes_file.write_text("\n".join(names) + "\n", encoding="utf-8")
        print(f"Added '{QR_NAME}' to classes.txt as id {names.index(QR_NAME)}")
    qr_id = names.index(QR_NAME)

    scanned, images_with_qr, added = 0, 0, 0
    for img_path in sorted(images_dir.iterdir()):
        if img_path.suffix.lower() not in IMG_EXTS:
            continue
        image = cv2.imread(str(img_path))
        if image is None:
            continue
        scanned += 1
        h, w = image.shape[:2]
        found = find_qr_boxes(image)
        if not found:
            continue
        images_with_qr += 1

        label_path = labels_dir / f"{img_path.stem}.txt"
        lines = label_path.read_text(encoding="utf-8").splitlines() if label_path.is_file() else []
        existing = []
        for line in lines:
            p = line.split()
            if len(p) == 5 and int(p[0]) == qr_id:
                xc, yc, bw, bh = (float(v) for v in p[1:])
                existing.append(((xc - bw / 2) * w, (yc - bh / 2) * h, (xc + bw / 2) * w, (yc + bh / 2) * h))

        new_lines = []
        for x1, y1, x2, y2 in found:
            x1, y1 = max(0.0, x1), max(0.0, y1)
            x2, y2 = min(float(w), x2), min(float(h), y2)
            if x2 - x1 < 4 or y2 - y1 < 4:
                continue
            if any(iou((x1, y1, x2, y2), e) > 0.5 for e in existing):
                continue
            new_lines.append(f"{qr_id} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} "
                             f"{(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}")
        added += len(new_lines)
        if new_lines and not args.dry_run:
            label_path.write_text("\n".join([l for l in lines if l.strip()] + new_lines) + "\n", encoding="utf-8")

    mode = "would add" if args.dry_run else "added"
    print(f"Images scanned: {scanned}, images with a QR code: {images_with_qr}, boxes {mode}: {added}")


if __name__ == "__main__":
    main()
