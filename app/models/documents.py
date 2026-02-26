from fastapi import UploadFile
from pydantic import BaseModel, Field
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
    risk_level: str
    risk_reasoning: str

class DocumentSummarizationModel(BaseModel):
    summary: str = Field(description="1-paragraph summary of the document including parties and core purpose.")
    risk_level: str = Field(description="risk level of the document, either LOW | MEDIUM | HIGH ")
    risk_reasoning: str = Field(description="reasoning for the risk level")