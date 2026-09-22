try:
    import easyocr
    HAS_EASYOCR = True
except ImportError:
    HAS_EASYOCR = False

class OCRService:
    def __init__(self):
        if HAS_EASYOCR:
            self.reader = easyocr.Reader(['hi', 'en'], gpu=False)
        else:
            self.reader = None
    
    def extract_text(self, image_path: str) -> tuple:
        if not self.reader:
            return "OCR not available", 0.0
        try:
            results = self.reader.readtext(image_path)
            text = "\n".join([line[1] for line in results])
            confidence = sum([line[2] for line in results]) / len(results) if results else 0.0
            return text, confidence
        except:
            return "", 0.0
    
    def detect_document_type(self, text: str) -> tuple:
        text_lower = text.lower()
        types = {
            "CASTE_CERTIFICATE": ["caste", "st", "sc", "obc", "tehsildar"],
            "INCOME_CERTIFICATE": ["income", "annual", "rupees"],
            "MARK_SHEET": ["marks", "grade", "examination"],
            "AADHAAR": ["aadhaar", "enrolment"],
        }
        best_type, best_score = "UNKNOWN", 0.0
        for dtype, keywords in types.items():
            score = sum(1 for kw in keywords if kw in text_lower) / len(keywords)
            if score > best_score:
                best_type, best_score = dtype, score
        return best_type, best_score
    
    def assess_document_quality(self, image_path: str) -> dict:
        return {"quality_score": 0.85, "issues": []}

ocr_service = OCRService()
