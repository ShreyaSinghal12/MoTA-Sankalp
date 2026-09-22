"""Install trained weights into the backend (detector_service switches to REAL_MODEL) and export ONNX.

python training/yolo/export.py                  # finetune weights if present, else base
python training/yolo/export.py path/to/best.pt  # any explicit weights file
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DST = HERE.parents[1] / "backend" / "models" / "document_detector.pt"


def pick_source() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    for stage in ("finetune", "base"):
        p = HERE / "runs" / stage / "weights" / "best.pt"
        if p.exists():
            return p
    return HERE / "runs" / "base" / "weights" / "best.pt"


if __name__ == "__main__":
    src = pick_source()
    if not src.exists():
        sys.exit(f"Weights not found: {src}")
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DST)
    print(f"Copied {src} -> {DST}")
    try:
        from ultralytics import YOLO
        print("Model classes:", YOLO(str(DST)).names)
        print("ONNX export:", YOLO(str(DST)).export(format="onnx", imgsz=960))
    except Exception as exc:
        print("ONNX export skipped:", exc)
    print("Restart the backend: /api/v1/health should show detector_model_present = true")
