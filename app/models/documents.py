from fastapi import UploadFile
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .document_types import DocumentTypeResponse

class DocumentUpload(BaseModel):
    filename: str
    file: UploadFile

class DocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    document_type: Optional['DocumentTypeResponse'] = None
    ai_progress: Optional[str] = "Pending"
    summary: Optional[str]= None
    
    class Config:
        from_attributes = True

class DocumentDetailResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    document_type: Optional['DocumentTypeResponse'] = None
    ai_progress: Optional[str] = "Pending"
    summary: Optional[str]= None
    file_path: str