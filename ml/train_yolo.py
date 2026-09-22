"""
train_yolo.py

Fine-tunes YOLOv8-nano on the MoTA-SANKALP certificate dataset and reports
metrics measured on the held-out TEST split (real images only).

Two ways to use it:

  A) One stage, from COCO weights (simplest):
     python train_yolo.py --data datasets/mota_mix/data.yaml --name real_v1

  B) Two stages (recommended when real data is small):
     Stage 1 - you already have this: synthetic model best.pt
     Stage 2 - fine-tune it on real data with a lower learning rate
               and a frozen backbone:
     python train_yolo.py --data datasets/mota_real/data.yaml \
         --weights runs_mota/synthetic/weights/best.pt \
         --lr0 0.0005 --freeze 10 --name real_finetune_v1

Output:
  runs_mota/<name>/weights/best.pt      model for the backend
  runs_mota/<name>/weights/best.onnx    (with --onnx)
  runs_mota/<name>/test_metrics.json    the numbers you may quote
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import torch
from ultralytics import YOLO

HACKATHON_MAP50 = 0.85
PRODUCTION_MAP50 = 0.94
CRITICAL_RECALL = 0.97
CRITICAL_CLASSES = ["official_seal", "tehsildar_sign"]


def train(args):
    device = 0 if torch.cuda.is_available() else "cpu"
    print(f"Device: {'GPU ' + torch.cuda.get_device_name(0) if device == 0 else 'CPU'}")
    print(f"Starting weights: {args.weights}")

    model = YOLO(args.weights)
    model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
        project=args.project,
        name=args.name,
        exist_ok=True,
        seed=args.seed,
        deterministic=True,
        patience=args.patience,
        optimizer="AdamW",
        lr0=args.lr0,
        weight_decay=0.0005,
        warmup_epochs=3,
        freeze=args.freeze if args.freeze > 0 else None,
        workers=args.workers,
        # Document-safe augmentation:
        # no flips - a mirrored seal or signature does not exist in reality
        fliplr=0.0,
        flipud=0.0,
        degrees=3.0,          # slight tilt, like a phone photo
        translate=0.05,
        scale=0.3,
        shear=1.0,
        perspective=0.0005,   # mild keystone from hand-held capture
        hsv_h=0.01,
        hsv_s=0.4,            # faded or saturated stamp ink
        hsv_v=0.4,            # lighting differences
        mosaic=0.5,
        close_mosaic=10,      # last 10 epochs on whole, un-mosaicked pages
        mixup=0.0,
        plots=True,
    )
    return Path(args.project) / args.name / "weights" / "best.pt"


def evaluate(best_path, args):
    """Evaluate on the TEST split and save the numbers to JSON."""
    model = YOLO(str(best_path))
    m = model.val(data=args.data, split="test", imgsz=args.imgsz,
                  batch=args.batch, project=args.project,
                  name=f"{args.name}_test", exist_ok=True, plots=True)

    names = model.names
    per_class = {}
    for i, cls_idx in enumerate(m.box.ap_class_index):
        p, r, ap50, ap = m.box.class_result(i)
        per_class[names[int(cls_idx)]] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "mAP50": round(float(ap50), 4),
            "mAP50_95": round(float(ap), 4),
        }

    result = {
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
        "weights": str(best_path),
        "data": args.data,
        "split": "test",
        "overall": {
            "precision": round(float(m.box.mp), 4),
            "recall": round(float(m.box.mr), 4),
            "mAP50": round(float(m.box.map50), 4),
            "mAP50_95": round(float(m.box.map), 4),
        },
        "per_class": per_class,
        "inference_ms_per_image": round(float(m.speed["inference"]), 2),
        "note": "Per-class recall is at the confidence threshold that maximises F1.",
    }

    out_json = Path(args.project) / args.name / "test_metrics.json"
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result, out_json


def report(result, out_json):
    o = result["overall"]
    print("\n" + "=" * 64)
    print("TEST SPLIT RESULTS (real images never seen in training)")
    print("=" * 64)
    print(f"{'class':<16}{'P':>8}{'R':>8}{'mAP50':>8}{'mAP50-95':>10}")
    for name, c in result["per_class"].items():
        print(f"{name:<16}{c['precision']:>8.3f}{c['recall']:>8.3f}"
              f"{c['mAP50']:>8.3f}{c['mAP50_95']:>10.3f}")
    print("-" * 64)
    print(f"{'ALL':<16}{o['precision']:>8.3f}{o['recall']:>8.3f}"
          f"{o['mAP50']:>8.3f}{o['mAP50_95']:>10.3f}")
    print(f"Inference: {result['inference_ms_per_image']} ms/image on this machine")

    print("\nAcceptance check:")
    print(f"  mAP50 >= {HACKATHON_MAP50} (hackathon):  "
          f"{'PASS' if o['mAP50'] >= HACKATHON_MAP50 else 'FAIL'}")
    print(f"  mAP50 >= {PRODUCTION_MAP50} (production): "
          f"{'PASS' if o['mAP50'] >= PRODUCTION_MAP50 else 'FAIL'}")
    for cls in CRITICAL_CLASSES:
        c = result["per_class"].get(cls)
        if c is None:
            print(f"  {cls} recall: NOT MEASURED (no test boxes)")
        else:
            ok = c["recall"] >= CRITICAL_RECALL
            print(f"  {cls} recall >= {CRITICAL_RECALL}: {'PASS' if ok else 'FAIL'} "
                  f"(recall {c['recall']:.3f}, precision {c['precision']:.3f})")
            if ok and c["precision"] < 0.5:
                print(f"    WARNING: {cls} recall is high only because precision is very low; "
                      "the model is over-predicting. Do not treat this as a pass.")
    print(f"\nSaved: {out_json}")


def main():
    ap = argparse.ArgumentParser(description="Fine-tune YOLOv8 for MoTA-SANKALP")
    ap.add_argument("--data", required=True, help="data.yaml from prepare_dataset.py")
    ap.add_argument("--weights", default="yolov8n.pt",
                    help="Starting weights: yolov8n.pt or your synthetic best.pt")
    ap.add_argument("--name", default="real_v1")
    ap.add_argument("--project", default="runs_mota")
    ap.add_argument("--epochs", type=int, default=150)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--lr0", type=float, default=0.001)
    ap.add_argument("--freeze", type=int, default=0,
                    help="Freeze first N layers (10 = backbone). Use for small datasets.")
    ap.add_argument("--patience", type=int, default=30)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--onnx", action="store_true", help="Also export best.onnx")
    ap.add_argument("--eval-only", help="Skip training; evaluate this best.pt")
    args = ap.parse_args()

    best = Path(args.eval_only) if args.eval_only else train(args)
    result, out_json = evaluate(best, args)
    report(result, out_json)

    if args.onnx:
        onnx_path = YOLO(str(best)).export(format="onnx", imgsz=args.imgsz)
        print(f"ONNX exported: {onnx_path}")


if __name__ == "__main__":
    main()
