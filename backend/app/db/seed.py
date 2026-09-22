"""Seed users, 6 demo applications (one per scenario) and synthetic certificate images.

Run standalone:  python -m app.db.seed          (seeds only if the DB is empty)
Reset:           delete backend/mota_sankalp.db and backend/uploads/*, then restart the API.
"""
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

from app.core.config import settings
from app.core.security import hash_password
from app.db.database import SessionLocal, init_db
from app.ml import duplicate_service
from app.models.models import Application, Document, User
from app.services import audit_service

# ---------------------------------------------------------------- rendering


def _font(size: int):
    for name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


TITLES = {
    "ST_CERTIFICATE": "SCHEDULED TRIBE CERTIFICATE",
    "INCOME_CERTIFICATE": "INCOME CERTIFICATE",
    "MARKSHEET": "STATEMENT OF MARKS",
    "ADMISSION_LETTER": "OFFER OF ADMISSION",
}


def render_document(path: Path, doc_type: str, lines: list[str], layout_seed: str,
                    seal: bool = True, signature: bool = True, qr: bool = True) -> str:
    """Draws a synthetic certificate. Visual layout depends on layout_seed (so pHash differs between
    genuinely different documents), while the text layer is embedded for OCR demo-fallback."""
    rng = random.Random(layout_seed)
    W, H = 1000, 1300
    palette = [(11, 61, 46), (70, 40, 120), (140, 60, 20), (20, 70, 130), (90, 90, 20)]
    band = rng.choice(palette)
    img = Image.new("RGB", (W, H), (250, 248, 240))
    d = ImageDraw.Draw(img)

    # big layout blocks drive the perceptual hash
    band_h = rng.randint(120, 260)
    d.rectangle([0, 0, W, band_h], fill=band)
    for _ in range(rng.randint(3, 5)):
        x0, y0 = rng.randint(0, W - 300), rng.randint(band_h + 50, H - 300)
        shade = rng.randint(150, 230)
        if rng.random() < 0.5:
            d.ellipse([x0, y0, x0 + rng.randint(200, 420), y0 + rng.randint(200, 420)], fill=(shade, shade, shade - 10))
        else:
            d.rectangle([x0, y0, x0 + rng.randint(200, 500), y0 + rng.randint(120, 300)], fill=(shade, shade - 5, shade))
    side = rng.choice(["left", "right", "none"])
    if side != "none":
        x = 0 if side == "left" else W - 70
        d.rectangle([x, band_h, x + 70, H], fill=tuple(min(255, c + 120) for c in band))
    d.rectangle([12, 12, W - 12, H - 12], outline=band, width=rng.choice([4, 8, 12]))

    d.text((50, 40), "GOVERNMENT OF INDIA  (SYNTHETIC DEMO DOCUMENT)", fill=(255, 255, 255), font=_font(26))
    d.text((50, 80), TITLES.get(doc_type, doc_type), fill=(255, 255, 255), font=_font(40))

    body_font = _font(30)
    y = band_h + rng.randint(60, 120)
    x_text = 110 if side == "left" else 60
    for line in lines:
        d.text((x_text, y), line, fill=(20, 20, 20), font=body_font)
        y += 58

    if seal:
        cx, cy = rng.randint(140, 420), rng.randint(H - 330, H - 200)
        for r in (95, 80):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(200, 30, 30), width=6)
        d.text((cx - 55, cy - 12), "OFFICIAL", fill=(200, 30, 30), font=_font(26))
    if signature:
        sx, sy = rng.randint(560, 700), rng.randint(H - 300, H - 220)
        pts = [(sx + i * 12, sy + int(22 * ((-1) ** i)) + rng.randint(-8, 8)) for i in range(18)]
        d.line(pts, fill=(20, 40, 190), width=5)
        d.text((sx, sy + 45), "Issuing Authority", fill=(20, 20, 20), font=_font(22))
    if qr:
        qx, qy, cell = W - 230, band_h + 30, 10
        for i in range(17):
            for j in range(17):
                if rng.random() < 0.5:
                    d.rectangle([qx + i * cell, qy + j * cell, qx + (i + 1) * cell - 1, qy + (j + 1) * cell - 1], fill=(0, 0, 0))
        for fx, fy in ((0, 0), (12, 0), (0, 12)):
            d.rectangle([qx + fx * cell, qy + fy * cell, qx + (fx + 5) * cell - 1, qy + (fy + 5) * cell - 1], outline=(0, 0, 0), width=cell)

    meta = PngInfo()
    meta.add_text("ocr_text", "\n".join([TITLES.get(doc_type, doc_type)] + lines))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, pnginfo=meta)
    return str(path)


def st_lines(name, cert_no, tribe, state, date):
    return [f"Certificate No: {cert_no}", f"Name: {name}", f"Category: ST ({tribe})",
            "This is to certify that the above person belongs to a Scheduled Tribe",
            f"State: {state}", f"Date: {date}"]


def income_lines(name, cert_no, income, date):
    return [f"Certificate No: {cert_no}", f"Name: {name}", f"Annual Income: Rs. {income:,.0f}",
            "Source: Agriculture and daily wages", f"Date: {date}"]


def marks_lines(name, roll, pct, course):
    return [f"Roll No: {roll}", f"Name of Candidate: {name}", f"Programme: {course}",
            f"Percentage: {pct}%", "Result: PASS"]


def admission_lines(name, uni, course, fee):
    return [f"Name: {name}", f"University: {uni}", f"Programme: {course}",
            f"Tuition and living cost: Rs. {fee:,.0f}", "Date: 15-05-2026"]


# ---------------------------------------------------------------- data

USERS = [
    ("admin@mota.gov.in", "MoTA Administrator", "admin123", "ADMIN"),
    ("officer@mota.gov.in", "Scrutiny Officer (Demo)", "officer123", "SCRUTINY_OFFICER"),
]

APPS = [
    dict(key="clean", full_name="Ravi Oraon", applicant_id="STU-JH-100001", gender="M", tribe="Oraon", state="Jharkhand",
         age=26, scheme_id="NFST", annual_income=320000, marks_percentage=72.4, claimed_fee=444000,
         course="Ph.D Chemistry", institution="Central University of Jharkhand", is_pvtg=False),
    dict(key="income_fail", full_name="Sunita Gond", applicant_id="STU-MP-100002", gender="F", tribe="Gond",
         state="Madhya Pradesh", age=27, scheme_id="NFST", annual_income=950000, marks_percentage=68.0,
         claimed_fee=444000, course="Ph.D Sociology", institution="Barkatullah University", is_pvtg=False),
    dict(key="name_mismatch", full_name="Anjali Kumari Munda", applicant_id="STU-JH-100003", gender="F", tribe="Munda",
         state="Jharkhand", age=25, scheme_id="NFST", annual_income=280000, marks_percentage=74.0,
         claimed_fee=444000, course="Ph.D Botany", institution="Ranchi University", is_pvtg=False),
    dict(key="duplicate", full_name="Birsa Hansda", applicant_id="STU-OD-100004", gender="M", tribe="Santal",
         state="Odisha", age=28, scheme_id="NOS", annual_income=410000, marks_percentage=71.0,
         claimed_fee=2600000, course="MSc Data Science", institution="University of Leeds (demo)", is_pvtg=False),
    dict(key="anomaly", full_name="Kiran Baiga", applicant_id="STU-CG-100005", gender="M", tribe="Baiga",
         state="Chhattisgarh", age=19, scheme_id="NOS", annual_income=15000, marks_percentage=99.2,
         claimed_fee=9800000, course="MS Aerospace", institution="Stanford University (demo)", is_pvtg=True),
    dict(key="missing_doc", full_name="Meena Bhil", applicant_id="STU-RJ-100006", gender="F", tribe="Bhil",
         state="Rajasthan", age=24, scheme_id="NOS", annual_income=350000, marks_percentage=78.0,
         claimed_fee=2200000, course="MA Development Studies", institution="University of Sussex (demo)", is_pvtg=False),
]


def _docs_for(a: dict, idx: int) -> list[tuple]:
    """Returns (doc_type, lines, layout_seed) per document for one seed application."""
    name = a["full_name"]
    st_name = "Anjali K. Munda" if a["key"] == "name_mismatch" else name
    docs = [
        ("ST_CERTIFICATE", st_lines(st_name, f"ST/{a['state'][:2].upper()}/2024/{4500 + idx:06d}", a["tribe"], a["state"], "12-03-2024"), f"st-{name}"),
        ("INCOME_CERTIFICATE", income_lines(name, f"INC/{a['state'][:2].upper()}/2025/{7800 + idx:06d}", a["annual_income"], "02-01-2025"),
         # duplicate case: same template/scan as Ravi Oraon's income certificate with edited text
         "inc-Ravi Oraon" if a["key"] == "duplicate" else f"inc-{name}"),
        ("MARKSHEET", marks_lines(name, f"20{19 + idx}{100 + idx}", a["marks_percentage"], "M.Sc / PG"), f"mk-{name}"),
    ]
    if a["scheme_id"] == "NOS" and a["key"] != "missing_doc":
        docs.append(("ADMISSION_LETTER", admission_lines(name, a["institution"], a["course"], a["claimed_fee"]), f"adm-{name}"))
    return docs


def make_sample_docs():
    """Documents for the live 'create + upload' demo (applicant: Priya Soren)."""
    out = settings.GENERATED_DIR / "sample_docs"
    render_document(out / "priya_soren_st_certificate.png", "ST_CERTIFICATE",
                    st_lines("Priya Soren", "ST/JH/2025/009911", "Santal", "Jharkhand", "05-02-2025"), "st-priya")
    render_document(out / "priya_soren_income_certificate.png", "INCOME_CERTIFICATE",
                    income_lines("Priya Soren", "INC/JH/2025/004411", 300000, "10-02-2025"), "inc-priya")
    render_document(out / "priya_soren_marksheet.png", "MARKSHEET",
                    marks_lines("Priya Soren", "2021777", 76.5, "M.Sc / PG"), "mk-priya")
    return out


def seed(force: bool = False):
    init_db()
    db = SessionLocal()
    try:
        if db.query(User).count() > 0 and not force:
            return False
        for email, name, pwd, role in USERS:
            db.add(User(email=email, full_name=name, hashed_password=hash_password(pwd), role=role))
        db.flush()

        for idx, a in enumerate(APPS, start=1):
            data = {k: v for k, v in a.items() if k != "key"}
            app = Application(**data, category="ST", source="SEED", status="RECEIVED",
                              application_number=f"{a['scheme_id']}-2026-{idx:05d}",
                              email=f"{a['full_name'].split()[0].lower()}@example.org", phone=f"90000000{idx:02d}")
            db.add(app)
            db.flush()
            audit_service.log(db, app.id, "APPLICATION_CREATED", "SEED", {"scenario": a["key"]}, commit=False)
            folder = settings.UPLOAD_DIR / str(app.id)
            if folder.exists():
                shutil.rmtree(folder)
            for doc_type, lines, layout in _docs_for(a, idx):
                path = folder / f"{doc_type.lower()}.png"
                render_document(path, doc_type, lines, layout, qr=doc_type != "MARKSHEET")
                doc = Document(application_id=app.id, doc_type=doc_type, filename=path.name, file_path=str(path),
                               content_type="image/png", size_bytes=path.stat().st_size,
                               phash=duplicate_service.compute_phash(str(path)))
                db.add(doc)
                db.flush()
                audit_service.log(db, app.id, "DOCUMENT_UPLOADED", "SEED",
                                  {"document_id": doc.id, "doc_type": doc_type}, commit=False)
        db.commit()
        make_sample_docs()
        return True
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeded." if seed() else "Database already seeded - nothing to do.")
