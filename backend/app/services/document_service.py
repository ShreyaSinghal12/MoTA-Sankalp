import os
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile
from datetime import datetime

class DocumentService:
    UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
    ALLOWED_TYPES = {
        "AADHAAR": ["pdf", "jpg", "jpeg", "png"],
        "INCOME_CERTIFICATE": ["pdf", "jpg", "jpeg", "png"],
        "CASTE_CERTIFICATE": ["pdf", "jpg", "jpeg", "png"],
        "MARK_SHEET": ["pdf", "jpg", "jpeg", "png"],
        "OVERSEAS_ADMISSION_LETTER": ["pdf", "jpg", "jpeg", "png"],
        "LANGUAGE_PROFICIENCY": ["pdf", "jpg", "jpeg", "png"]
    }
    
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    @staticmethod
    def validate_document_type(doc_type: str) -> bool:
        return doc_type in DocumentService.ALLOWED_TYPES
    
    @staticmethod
    def validate_file_extension(filename: str, doc_type: str) -> bool:
        ext = filename.split(".")[-1].lower()
        return ext in DocumentService.ALLOWED_TYPES.get(doc_type, [])
    
    @staticmethod
    async def save_document(
        file: UploadFile,
        doc_type: str,
        applicant_id: int,
        application_id: int
    ) -> Tuple[bool, str, Optional[str]]:
        if not DocumentService.validate_document_type(doc_type):
            return False, f"Invalid document type: {doc_type}", None
        
        if not DocumentService.validate_file_extension(file.filename, doc_type):
            return False, f"Invalid file extension for {doc_type}", None
        
        content = await file.read()
        if len(content) > DocumentService.MAX_FILE_SIZE:
            return False, f"File size exceeds {DocumentService.MAX_FILE_SIZE / 1024 / 1024}MB limit", None
        
        app_dir = DocumentService.UPLOAD_DIR / f"app_{application_id}"
        app_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{applicant_id}_{doc_type}_{timestamp}.{file.filename.split('.')[-1]}"
        file_path = app_dir / filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        return True, "Document uploaded successfully", str(file_path)
    
    @staticmethod
    def get_application_documents(application_id: int) -> list:
        app_dir = DocumentService.UPLOAD_DIR / f"app_{application_id}"
        if not app_dir.exists():
            return []
        
        documents = []
        for file in app_dir.iterdir():
            if file.is_file():
                documents.append({
                    "file_name": file.name,
                    "file_size": file.stat().st_size,
                    "file_path": str(file),
                    "uploaded_at": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
        
        return documents
    
    @staticmethod
    def delete_document(file_path: str) -> Tuple[bool, str]:
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True, "Document deleted successfully"
            return False, "Document not found"
        except Exception as e:
            return False, f"Error deleting document: {str(e)}"