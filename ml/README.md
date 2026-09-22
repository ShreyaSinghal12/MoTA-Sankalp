# MoTA-SANKALP: Training the certificate detector

No Roboflow and no external inference API. The trained model runs locally in the backend.

Classes (this exact order everywhere):

| id | class | what to box | where the data comes from |
|----|-------|-------------|---------------------------|
| 0 | official_seal | Rubber stamp / embossed seal of the issuing office | Kaggle Stamp-Data, StaVer + own certificates |
| 1 | tehsildar_sign | Signature of the issuing officer | Kaggle SignverOD + own certificates |
| 2 | income_box | The region stating the annual income amount | Own certificates only |
| 3 | st_box | The region stating the tribe / ST category | Own certificates only |
| 4 | qr_code | Any QR code | Auto-labelled with OpenCV (autolabel_qr.py) |

No public dataset contains `income_box` or `st_box`, so your own annotated certificates are required.
Kaggle data teaches the model what seals and signatures look like in general. Your certificates teach it Indian certificate layouts, and they are the only images used for the test score.

## Scripts

| Script | Purpose |
|--------|---------|
| inspect_dataset.py | Shows the format and class names of any downloaded dataset. Run it first. |
| convert_to_yolo.py | COCO / VOC / YOLO / CSV / masks -> canonical 5-class layout, mapping classes by name |
| autolabel_qr.py | Adds qr_code boxes using OpenCV |
| prepare_dataset.py | Merges sources, validates labels, splits by certificate; --test-from = your certificates |
| train_yolo.py | Fine-tunes YOLOv8n and reports test-split metrics to test_metrics.json |
| kaggle_train.ipynb | Runs all of the above on a free Kaggle T4 GPU |

## Kaggle datasets used

| Kaggle dataset | Content | Map to |
|----------------|---------|--------|
| victordibia/signverod | 2,765 scanned documents with signature, initials, redaction, date boxes | signature=tehsildar_sign |
| aravindnagarajan/stamp-data | Stamp bounding boxes | stamp=official_seal (confirm the name with inspect_dataset.py) |
| rtatman/stamp-verification-staver-dataset | Scanned documents with stamps (large download) | official_seal (format: check with inspect_dataset.py) |

Check each dataset's licence on its Kaggle page before any use beyond the hackathon.

Known limitation (partial labels): SignverOD labels only signatures, so any stamp in those images counts as background. The same is true for signatures in the stamp datasets. That can lower recall. Mix in enough of your own fully-labelled certificates, and if recall on the test split is low, ask for the cross-labelling step.

## Step 1 - Collect real certificate images

Sources that don't need any third-party platform:

1. **Team members, friends, and family (with written consent).** Caste, income, and domicile certificates and mark sheets.
2. **Your own DigiLocker-issued PDFs.** Convert the pages to images. These usually carry QR codes and digital signature blocks.
3. **Public sample or blank formats** from state e-District portals. Useful for layout variety, but they often have no seal or signature.

Privacy rules (these are real people's documents):

- Black out Aadhaar numbers, photos, and addresses **before** annotating. Masking them doesn't affect seal or signature detection.
- Never commit images to Git. Add `exports/` and `datasets/` to `.gitignore`.
- Colab uploads data to Google. Only use Colab for images that are consented and masked. Otherwise train locally.

Capture each physical certificate 3-5 ways: flatbed scan, phone photo straight on, slight tilt, dim light, and a crumpled or folded copy. This variety matters more than raw volume.

**File naming is required for an honest test score.** Name every photo of the same certificate with a shared prefix and `__`:

```
cert001__scan.jpg   cert001__phone.jpg   cert001__tilt.jpg
cert002__scan.jpg   ...
```

`prepare_dataset.py` keeps all photos of one certificate in the same split. Otherwise the model could be tested on a certificate it already saw in training.

Rough target: at least 150 different certificates, and at least 100 boxes per class in the training split. `income_box` and `st_box` only appear on income and caste certificates, so collect enough of both.

## Step 2 - Annotate locally with Label Studio

Label Studio runs on localhost and stores data on your disk. Use a separate environment:

```
python -m venv ls-env
ls-env\Scripts\activate            (Windows)
pip install label-studio
label-studio start                 (opens http://localhost:8080)
```

Create a project, import the images, and use this labeling config:

```xml
<View>
  <Image name="image" value="$image"/>
  <RectangleLabels name="label" toName="image">
    <Label value="official_seal"/>
    <Label value="tehsildar_sign"/>
    <Label value="income_box"/>
    <Label value="st_box"/>
    <Label value="qr_code"/>
  </RectangleLabels>
</View>
```

Box rules (keep them consistent, because the model learns your habits):

- Draw tight boxes that include the whole stamp even where it overlaps text.
- Box every instance. Two seals means two boxes.
- Skip an object only if less than about a third of it is visible.
- `income_box` and `st_box`: box the line containing the value, not the whole paragraph.

When done: **Export -> YOLO**. Unzip into `exports/real/`, so you have `exports/real/images`, `exports/real/labels`, and `exports/real/classes.txt`.
The class order in `classes.txt` doesn't matter, because the prepare script remaps classes by name.

## Step 3 - Add Kaggle data and build the dataset

Easiest: upload `ml/` and your Label Studio export as private Kaggle datasets and run `kaggle_train.ipynb`.

Locally, download with the Kaggle CLI (needs `kaggle.json` from your Kaggle account settings):

```
pip install -r requirements.txt kaggle
kaggle datasets download -d victordibia/signverod -p ../kaggle/signverod --unzip
kaggle datasets download -d aravindnagarajan/stamp-data -p ../kaggle/stamp-data --unzip
```

Then inspect, convert, label QR codes, and merge:

```
python inspect_dataset.py ../kaggle/signverod
python inspect_dataset.py ../kaggle/stamp-data

python convert_to_yolo.py --src ../kaggle/signverod --out ../conv/signverod --prefix sv --map signature=tehsildar_sign --limit 1500
python convert_to_yolo.py --src ../kaggle/stamp-data --out ../conv/stamps --prefix st --map stamp=official_seal

python autolabel_qr.py --dir ../exports/real

python prepare_dataset.py --src ../conv/signverod ../conv/stamps \
    --test-from ../exports/real --out ../datasets/mota_mix
```

Use the class names that inspect_dataset.py printed in `--map`. `--test-from` means the test split comes only from your own certificates; your certificates also contribute to train and val.
Add `--synthetic ../exports/synthetic` to put your 450 synthetic images into train only. That folder needs `images/`, `labels/`, and a `classes.txt` with the 5 names in the order above.

Read the printed class table. Fix the annotation problems it lists (or use `--strict`), and pay attention to per-class warnings.

## Step 4 - Train and fine-tune

Option A, one stage from COCO weights on the mixed dataset:

```
python train_yolo.py --data ../datasets/mota_mix/data.yaml --name real_v1 --onnx
```

Option B, two stages (usually better with little real data). Fine-tune your synthetic model on real data with a frozen backbone and a lower learning rate:

```
python train_yolo.py --data ../datasets/mota_mix/data.yaml \
    --weights path/to/synthetic/best.pt --lr0 0.0005 --freeze 10 \
    --name real_finetune_v1 --onnx
```

On a CPU, add `--batch 8 --workers 0`. Training is slow on CPU, so prefer a GPU.

Colab (GPU runtime), after uploading `ml/` and `datasets/` to Drive:

```
from google.colab import drive; drive.mount('/content/drive')
%cd /content/drive/MyDrive/mota/ml
!pip install -q -r requirements.txt
!python train_yolo.py --data ../datasets/mota_mix/data.yaml --name real_v1 --onnx
```

Note: `data.yaml` stores an absolute `path:`. If you move the dataset to another machine, run `prepare_dataset.py` there again or edit that line.

## Step 5 - Read the results honestly

The script evaluates on the **test split** (real images the model never saw) and writes `runs_mota/<name>/test_metrics.json`. Only quote numbers from that file. It also prints PASS/FAIL against the blueprint targets (mAP50 >= 0.85 hackathon, >= 0.94 production, seal/signature recall >= 0.97).

If a class is weak, add more real examples of that class. Tweaking hyperparameters rarely fixes a data shortage.

## Step 6 - Use the model in the backend

```
copy runs_mota\real_v1\weights\best.pt  backend\models\best.pt
```

Restart the backend. `POST /api/v1/documents/analyze` then runs the model on each upload.
