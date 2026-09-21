from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentUploadSchema(BaseModel):
    document_type: str
    file_name: str
    file_size: int
    file_path: str
    uploaded_at: str

class ApplicationCreateSchema(BaseModel):
    scheme_id: str
    applicant_id: int
    category: str
    age: int
    annual_income: int
    qualification: str
    gender: str

class ApplicationUpdateSchema(BaseModel):
    status: Optional[str] = None

class ApplicationSchema(BaseModel):
    id: int
    scheme_id: str
    applicant_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    category: str
    age: int
    annual_income: int
    qualification: str
    gender: str

    class Config:
        from_attributes = True

class ApplicationDetailSchema(ApplicationSchema):
    documents: List[DocumentUploadSchema]
    evaluation_result: Optional[dict] = None