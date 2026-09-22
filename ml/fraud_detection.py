import imagehash
from PIL import Image
from sklearn.ensemble import IsolationForest
import numpy as np

class FraudDetector:
    def __init__(self):
        self.iso_forest = IsolationForest(contamination=0.05, random_state=42)
    
    def detect_document_forgery_phash(self, image_path1, image_path2):
        img1_hash = imagehash.phash(Image.open(image_path1))
        img2_hash = imagehash.phash(Image.open(image_path2))
        hamming_distance = img1_hash - img2_hash
        similarity = 1.0 - (hamming_distance / 64.0)
        is_duplicate = hamming_distance <= 10
        return {"similarity": similarity, "is_duplicate": is_duplicate, "distance": hamming_distance}
    
    def detect_anomaly(self, application_features):
        predictions = self.iso_forest.predict([application_features])
        anomaly_score = self.iso_forest.score_samples([application_features])
        is_anomaly = predictions[0] == -1
        return {"is_anomaly": is_anomaly, "anomaly_score": float(anomaly_score[0])}
    
    def fit_on_historical(self, historical_features):
        self.iso_forest.fit(historical_features)
        print("Anomaly detector trained on historical data")

if __name__ == "__main__":
    detector = FraudDetector()
    print("Fraud detection system initialized")
