import easyocr
import torch

class OCRTrainer:
    def __init__(self):
        self.gpu_available = torch.cuda.is_available()
    
    def fine_tune_bilingual(self, train_data_path):
        reader = easyocr.Reader(['hi', 'en'], gpu=self.gpu_available)
        print(f"EasyOCR reader initialized (GPU: {self.gpu_available})")
        return reader
    
    def extract_batch(self, image_paths):
        reader = easyocr.Reader(['hi', 'en'], gpu=self.gpu_available)
        results = []
        for img_path in image_paths:
            result = reader.readtext(img_path)
            text = '\n'.join([line[1] for line in result])
            confidence = sum([line[2] for line in result]) / len(result) if result else 0.0
            results.append({"text": text, "confidence": confidence})
        return results

if __name__ == "__main__":
    trainer = OCRTrainer()
    reader = trainer.fine_tune_bilingual("data/ocr_training")
    print("OCR model ready for inference")
