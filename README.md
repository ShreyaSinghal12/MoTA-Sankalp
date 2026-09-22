# MoTA-SANKALP

**Scheme Administration, Network & Knowledge Automated Lifecycle Platform**
Administrator-side scholarship / fellowship management for the Ministry of Tribal Affairs
(NFST and NOS). Smart India Hackathon 2026 - Problem Statement 239. End-to-end MVP.

> AI extracts, detects, compares, flags and explains.
> The rule engine checks policy.
> The officer makes the final decision.

## Features

| Stage | Implementation | Status in MVP |
|---|---|---|
| Admin login | JWT (python-jose) + bcrypt, roles ADMIN / SCRUTINY_OFFICER | Real |
| Dashboard | `/dashboard/stats` + React cockpit | Real |
| Applications | CRUD, filters, create form | Real |
| Import | NSP import + status sync | Mock adapter |
| Documents | Multipart upload, type/size validation, `backend/uploads/{id}/` | Real |
| OCR | EasyOCR (en+hi) if installed, else demo fallback reading the synthetic text layer | Real / fallback |
| Field extraction | Regex: name, income, certificate no, category, date, marks | Real |
| Visual detection | YOLOv8n `backend/models/document_detector.pt` if present (REAL_MODEL), else heuristic detector (DEMO_FALLBACK) | Real / fallback |
| Name matching | RapidFuzz with normalisation + initials check | Real |
| Duplicate detection | pHash (imagehash) Hamming distance vs earlier documents | Real |
| Anomaly detection | scikit-learn IsolationForest on synthetic normal records, saved to `generated/isolation_forest.joblib` | Real |
| Scheme rules | YAML (`configs/schemes/*.yaml`), generic evaluator | Real |
| Unified scrutiny | `POST /applications/{id}/scrutiny` | Real |
| MoTA-Twin | Deterministic discrepancy-resolution agent with reasoning steps | Real |
| Officer workflow | Approve / Reject / Manual review with mandatory reason, AI-override tracking | Real |
| Sanction | Sanction number + ReportLab PDF in `generated/sanctions/` | Real |
| Payment | PFMS DBT | Mock adapter |
| DigiLocker | Issuer-verified document metadata | Mock adapter |
| Audit | Every AI + human step in `audit_logs`, timeline UI | Real |

## Architecture

```
React (Vite) :5173  --REST/JWT-->  FastAPI :8000
                                     |- api/          auth, applications, schemes, scrutiny, officers, integrations, dashboard
                                     |- services/     rule_engine, document_service, scrutiny_service, sanction_service, audit_service
                                     |- ml/           ocr, detector (YOLO), fuzzy (RapidFuzz), duplicate (pHash), anomaly (IsolationForest)
                                     |- agents/       mota_twin (deterministic resolution)
                                     |- integrations/ nsp_mock, digilocker_mock, pfms_mock
                                     '- SQLAlchemy -> SQLite (mota_sankalp.db)   [PostgreSQL = change DATABASE_URL]
```

Scrutiny pipeline:
`documents -> OCR -> field extraction -> visual detection -> RapidFuzz -> pHash -> IsolationForest -> rule engine -> rule/risk results -> discrepancies -> MoTA-Twin proposals -> officer`

Tables: users, applications, documents, rule_results, risk_results, discrepancies, agent_resolutions,
officer_actions, sanctions, payments, audit_logs.

## Installation (Windows PowerShell)

```powershell
cd mota-sankalp\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Optional heavy ML (torch; the app works without it):
```powershell
pip install -r requirements-ml.txt
```

## Run backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```
- API root: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

On first start the DB is created, users + 6 demo applications + synthetic certificates are seeded,
and the Isolation Forest is trained. Reset: stop the server, delete `backend\mota_sankalp.db` and the numbered
folders in `backend\uploads\`, restart.

## Run frontend

```powershell
cd frontend
npm install
npm run dev
```
Open http://127.0.0.1:5173

## Demo accounts

| Email | Password | Role |
|---|---|---|
| admin@mota.gov.in | admin123 | ADMIN |
| officer@mota.gov.in | officer123 | SCRUTINY_OFFICER |

## Demo scenarios (seeded)

| ID | Applicant | Scheme | Scenario | Expected scrutiny result |
|---|---|---|---|---|
| 1 | Ravi Oraon | NFST | Clean | SCRUTINY_COMPLETED, RECOMMEND_APPROVE |
| 2 | Sunita Gond | NFST | Income Rs 9.5L > limit | ELIGIBILITY_FAILURE, RECOMMEND_REJECT |
| 3 | Anjali Kumari Munda | NFST | ST certificate says "Anjali K. Munda" | NAME_MISMATCH, Twin: ACCEPT_WITH_NOTE |
| 4 | Birsa Hansda | NOS | Income certificate reuses app 1's scan | POSSIBLE_DUPLICATE (Hamming 0) |
| 5 | Kiran Baiga | NOS | Age 19, income 15k, marks 99.2, claim 98L | ANOMALY (IsolationForest) |
| 6 | Meena Bhil | NOS | No admission letter | MISSING_DOCUMENT, Twin: FETCH_FROM_DIGILOCKER |

Live-upload demo files (applicant "Priya Soren") are generated in `backend/generated/sample_docs/`.

## Key API endpoints (all under /api/v1)

```
POST /auth/login                GET  /auth/me
GET  /dashboard/stats
GET  /schemes                   GET  /schemes/{id}           POST /schemes/{id}/evaluate
GET  /applications              POST /applications           GET/PATCH /applications/{id}
POST /applications/{id}/documents                            GET  /documents/{id}/file
POST /applications/{id}/scrutiny
POST /applications/{id}/twin/resolve/{discrepancy_id}
POST /applications/{id}/approve | /reject | /manual-review   (body: {"reason": "..."})
POST /applications/{id}/sanction                             GET  /sanctions/{id}/pdf
POST /sanctions/{id}/payment
GET  /applications/{id}/audit
POST /integrations/nsp/import   POST /integrations/nsp/status-sync
GET  /integrations/digilocker/{applicant_id}
GET  /ml/fuzzy?a=..&b=..        GET  /ml/anomaly?...
```

## ML pipeline notes

- **OCR**: env `OCR_ENGINE=auto|easyocr|fallback`. Fallback reads the text layer embedded in the synthetic demo PNGs so the flow runs without torch. Real scans need EasyOCR.
- **Detector**: output carries `mode` = `REAL_MODEL` or `DEMO_FALLBACK`, and every class carries its `source` (yolo / heuristic / ocr_keywords).
- **pHash**: flags near-identical images for verification; never auto-rejects.
- **IsolationForest**: features annual_income, marks_percentage, age, claimed_fee; returns NORMAL / NEEDS_REVIEW plus top deviating features.
- **Scheme values in YAML are demo values**, not official MoTA figures.

## YOLO training (real data, two-stage fine-tuning)

The detector is trained on **real** public data, then fine-tuned on your own annotated certificates.
No synthetic images are used.

| Class | Source | Notes |
|---|---|---|
| signature | Ultralytics Signature dataset (178 real scanned/photographed documents) | auto-download |
| qr_code | Kaggle `hamidl/yoloqrlabeled` | real photos, YOLO labels |
| official_seal | Kaggle `aravindnagarajan/stamp-data` | documents with stamp boxes |
| income_field, st_certificate_field | your own annotated Indian certificates only | no public dataset exists; OCR keywords cover these until you add data |

```powershell
pip install -r training/yolo/requirements.txt          # ultralytics + kaggle
# put kaggle.json in C:\Users\<you>\.kaggle\ (kaggle.com -> Settings -> API -> Create New Token)
python training/yolo/download_datasets.py
python training/yolo/prepare_dataset.py --inspect      # check class names -> fix class_map in sources.yaml if needed
python training/yolo/prepare_dataset.py --stage base
python training/yolo/preview_labels.py --stage base    # eyeball boxes in training/yolo/preview/base/
python training/yolo/train.py --stage base --device 0  # GPU (Colab T4); use --device cpu otherwise
python training/yolo/evaluate.py --stage base --device 0
# optional stage 2: annotate 50-150 real certificates (LabelImg/CVAT, YOLO format, same 5 class names)
# into training/yolo/raw/own_certificates/{images,labels}/ + classes.txt, then:
python training/yolo/prepare_dataset.py --stage finetune
python training/yolo/train.py --stage finetune --device 0
python training/yolo/evaluate.py --stage finetune --device 0
python training/yolo/export.py                         # -> backend/models/document_detector.pt (+ ONNX)
```

`prepare_dataset.py` auto-detects YOLO txt, Pascal VOC xml and COCO json, remaps class names via
`sources.yaml`, merges sources, and makes a deterministic 70/15/15 train/val/test split. Metrics are
reported on the held-out **test** split.

Known limitation: each public dataset labels only its own object type (e.g. a stamp image may contain an
unlabelled signature). Stage-2 fine-tuning on fully annotated certificates corrects most of this.

## Tests

```powershell
cd backend
pytest
```
Covers health/auth, rule engine, RapidFuzz, pHash, IsolationForest, unified scrutiny for all 6 scenarios,
MoTA-Twin, the full approve -> sanction -> PFMS -> audit flow, uploads, and mock integrations.

## Future production deployment (not in MVP)

- PostgreSQL 16 (`DATABASE_URL`) + Alembic migrations
- MinIO / S3 object storage for documents; Redis + Celery for async scrutiny
- Keycloak / Parichay SSO, full RBAC (Ministry / State / District nodal officers, auditor)
- Real NSP, DigiLocker, PFMS, DBT, UIDAI (Aadhaar vault + masking), e-Sign
- Fine-tuned YOLO + bilingual OCR served via ONNX Runtime; local LLM (Ollama) only for wording MoTA-Twin explanations
- Kubernetes on NIC MeghRaj, Prometheus + Grafana, TLS, DPDP Act 2023 compliance, immutable audit store
