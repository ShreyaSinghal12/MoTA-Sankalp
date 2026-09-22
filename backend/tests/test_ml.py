from PIL import Image, ImageDraw

from app.ml import anomaly_service, duplicate_service, fuzzy_service


def test_rapidfuzz_exact_and_initial():
    assert fuzzy_service.compare_names("Ravi Oraon", "RAVI  ORAON.")["interpretation"] == "MATCH"
    r = fuzzy_service.compare_names("Anjali Kumari Munda", "Anjali K. Munda")
    assert r["initials_consistent"] is True
    assert r["interpretation"] == "PROBABLE_MATCH_REVIEW"
    assert fuzzy_service.compare_names("Ravi Oraon", "Sunita Gond")["interpretation"] == "MISMATCH"


def test_phash_duplicate(tmp_path):
    a, b, c = tmp_path / "a.png", tmp_path / "b.png", tmp_path / "c.png"
    img = Image.new("RGB", (400, 400), "white")
    ImageDraw.Draw(img).ellipse([50, 50, 300, 300], fill="black")
    img.save(a)
    img.resize((380, 380)).save(b)  # re-scanned copy
    other = Image.new("RGB", (400, 400), "white")
    ImageDraw.Draw(other).rectangle([0, 200, 400, 400], fill="black")
    other.save(c)
    ha, hb, hc = (duplicate_service.compute_phash(str(p)) for p in (a, b, c))
    assert duplicate_service.hamming(ha, hb) <= 4
    res = duplicate_service.find_matches(ha, [{"document_id": 2, "phash": hb}, {"document_id": 3, "phash": hc}])
    assert res["possible_duplicate"] is True
    assert res["nearest"][0]["document_id"] == 2


def test_isolation_forest():
    normal = anomaly_service.score({"annual_income": 300000, "marks_percentage": 70, "age": 26, "claimed_fee": 440000})
    odd = anomaly_service.score({"annual_income": 15000, "marks_percentage": 99.2, "age": 19, "claimed_fee": 9800000})
    assert normal["label"] == "NORMAL"
    assert odd["label"] == "NEEDS_REVIEW"
    assert odd["anomaly_score"] < normal["anomaly_score"]
