"""Draw ground-truth boxes on a few images per split so you can eyeball the class mapping before training.

python training/yolo/preview_labels.py --stage base --n 12
Output: training/yolo/preview/<stage>/*.jpg
"""
import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
NAMES = ["official_seal", "signature", "qr_code", "income_field", "st_certificate_field"]
COLORS = [(220, 30, 30), (30, 60, 220), (20, 150, 60), (200, 120, 0), (140, 0, 160)]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="base")
    ap.add_argument("--n", type=int, default=12)
    args = ap.parse_args()
    root = HERE / "datasets" / f"mota_real_{args.stage}"
    out = HERE / "preview" / args.stage
    out.mkdir(parents=True, exist_ok=True)
    imgs = sorted((root / "images" / "train").iterdir())
    random.Random(0).shuffle(imgs)
    for img in imgs[: args.n]:
        lbl = root / "labels" / "train" / (img.stem + ".txt")
        with Image.open(img) as im:
            im = im.convert("RGB")
            W, H = im.size
            d = ImageDraw.Draw(im)
            for line in lbl.read_text().splitlines():
                c, cx, cy, w, h = line.split()
                c, cx, cy, w, h = int(c), float(cx) * W, float(cy) * H, float(w) * W, float(h) * H
                d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], outline=COLORS[c], width=max(2, W // 300))
                d.text((cx - w / 2 + 3, cy - h / 2 + 3), NAMES[c], fill=COLORS[c])
            im.save(out / (img.stem + ".jpg"))
    print(f"Wrote {min(args.n, len(imgs))} previews to {out}")
