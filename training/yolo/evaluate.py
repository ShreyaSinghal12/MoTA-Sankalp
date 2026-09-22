"""Evaluate a trained stage on its held-out TEST split (never seen during training or early-stopping).

python training/yolo/evaluate.py --stage base
python training/yolo/evaluate.py --stage finetune
"""
import argparse
from pathlib import Path

from ultralytics import YOLO

HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["base", "finetune"], default="base")
    ap.add_argument("--imgsz", type=int, default=960)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    weights = HERE / "runs" / args.stage / "weights" / "best.pt"
    model = YOLO(str(weights))
    m = model.val(data=str(HERE / f"dataset_{args.stage}.yaml"), split="test", imgsz=args.imgsz, device=args.device,
                  project=str(HERE / "runs"), name=f"{args.stage}_test", exist_ok=True)
    print(f"\nTEST split - {args.stage}")
    print(f"mAP@0.50      : {m.box.map50:.4f}")
    print(f"mAP@0.50:0.95 : {m.box.map:.4f}")
    print(f"Precision     : {m.box.mp:.4f}")
    print(f"Recall        : {m.box.mr:.4f}")
    print("Per class (only classes present in the test split):")
    for idx, cls_id in enumerate(m.box.ap_class_index):
        print(f"  {model.names[int(cls_id)]:22s} AP50={m.box.ap50[idx]:.4f}  AP50-95={m.box.ap[idx]:.4f}")
    print(f"\nPlots and confusion matrix: {HERE / 'runs' / (args.stage + '_test')}")
