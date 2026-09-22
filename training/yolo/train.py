"""Train the MoTA-SANKALP document detector on real data.

Stage 1 (base):     YOLOv8n (COCO-pretrained) -> public real data (signatures, QR codes, stamps)
Stage 2 (finetune): stage-1 best.pt -> public data + your own annotated Indian certificates,
                    lower learning rate, frozen backbone, so it adapts without forgetting.

python training/yolo/train.py --stage base --device 0
python training/yolo/train.py --stage finetune --device 0
"""
import argparse
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"

STAGES = {
    "base": dict(data="dataset_base.yaml", weights="yolov8n.pt", epochs=80, lr0=0.01, freeze=None),
    "finetune": dict(data="dataset_finetune.yaml", weights=str(RUNS / "base" / "weights" / "best.pt"),
                     epochs=40, lr0=0.002, freeze=10),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=STAGES, default="base")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--imgsz", type=int, default=960, help="documents have small objects; 960 beats 640")
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default="cpu", help="cpu | 0 for first GPU")
    ap.add_argument("--weights", help="override starting weights")
    args = ap.parse_args()

    cfg = STAGES[args.stage]
    data = HERE / cfg["data"]
    if not data.exists():
        raise SystemExit(f"{data.name} missing - run: python training/yolo/prepare_dataset.py --stage {args.stage}")
    weights = args.weights or cfg["weights"]
    if args.stage == "finetune" and not Path(weights).exists():
        raise SystemExit(f"Base weights not found at {weights} - run the base stage first")

    model = YOLO(weights)
    model.train(
        data=str(data),
        epochs=args.epochs or cfg["epochs"],
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        lr0=cfg["lr0"],
        freeze=cfg["freeze"],
        cos_lr=True,
        patience=20,
        project=str(RUNS),
        name=args.stage,
        exist_ok=True,
        # document-appropriate augmentation: no mirroring (text/QR are not symmetric),
        # small rotations and perspective like phone photos of paper
        fliplr=0.0,
        degrees=5.0,
        perspective=0.0005,
        scale=0.4,
        hsv_s=0.5,
        mosaic=0.7,
        close_mosaic=10,
    )
    print("Best weights:", RUNS / args.stage / "weights" / "best.pt")
    print(f"Next: python training/yolo/evaluate.py --stage {args.stage}")
