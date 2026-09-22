class FraudDetectionService:
    def detect_document_tampering(self, text: str, expected_keywords: list) -> dict:
        found = sum(1 for kw in expected_keywords if kw.lower() in text.lower())
        is_suspicious = found < len(expected_keywords) * 0.5
        return {
            "is_suspicious": is_suspicious,
            "tampering_score": 0.2 if is_suspicious else 0.05,
            "found_keywords": found,
            "missing_keywords": len(expected_keywords) - found,
            "confidence": 0.85
        }
    
    def check_for_forgery(self, document_text: str, expected_patterns: list) -> dict:
        matched = sum(1 for pattern in expected_patterns if pattern.lower() in document_text.lower())
        is_forged = matched < len(expected_patterns) * 0.3
        return {
            "is_forged": is_forged,
            "forgery_confidence": 0.15 if is_forged else 0.05,
            "matched_patterns": matched,
            "missing_patterns": len(expected_patterns) - matched,
            "pattern_match_score": matched / len(expected_patterns) if expected_patterns else 0.0
        }
    
    def detect_text_similarity(self, text1: str, text2: str) -> float:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, text1, text2).ratio()

fraud_detection_service = FraudDetectionService()
