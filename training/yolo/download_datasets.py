"""Download every enabled source in sources.yaml into training/yolo/raw/<key>/.

Kaggle sources need an API token:
  kaggle.com -> Settings -> API -> Create New Token  (downloads kaggle.json)
  Windows: put it at C:\\Users\\<you>\\.kaggle\\kaggle.json
  Colab:   upload it, then  !mkdir -p ~/.kaggle && cp kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json

python training/yolo/download_datasets.py            # all sources
python training/yolo/download_datasets.py --only kaggle_qr
"""
import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"


def download_url(url: str, dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    zpath = dest / "download.zip"
    print(f"  GET {url}")
    urllib.request.urlretrieve(url, zpath)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(dest)
    zpath.unlink()


def download_kaggle(slug: str, dest: Path):
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        raise SystemExit("pip install kaggle   (then place kaggle.json as described at the top of this file)")
    api = KaggleApi()
    api.authenticate()
    dest.mkdir(parents=True, exist_ok=True)
    print(f"  kaggle datasets download {slug}")
    api.dataset_download_files(slug, path=str(dest), unzip=True, quiet=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="download a single source key")
    ap.add_argument("--force", action="store_true", help="re-download even if folder exists")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(HERE / "sources.yaml", encoding="utf-8"))
    for src in cfg["sources"]:
        if src.get("enabled", True) is False or (args.only and src["key"] != args.only):
            continue
        dest = RAW / src["key"]
        if src["type"] == "local":
            status = "found" if (HERE / src["path"]).exists() else "MISSING (add your annotated images later)"
            print(f"[{src['key']}] local source {src['path']}: {status}")
            continue
        if dest.exists() and any(dest.iterdir()) and not args.force:
            print(f"[{src['key']}] already downloaded -> {dest}")
            continue
        if dest.exists():
            shutil.rmtree(dest)
        print(f"[{src['key']}] downloading ...")
        if src["type"] == "url":
            download_url(src["url"], dest)
        elif src["type"] == "kaggle":
            download_kaggle(src["slug"], dest)
        else:
            raise SystemExit(f"unknown source type {src['type']}")
        print(f"[{src['key']}] done -> {dest}")
    print("\nNext: python training/yolo/prepare_dataset.py --inspect")


if __name__ == "__main__":
    main()
