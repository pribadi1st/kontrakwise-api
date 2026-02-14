from fastapi import UploadFile
from pydantic import BaseModel
from datetime import datetime

class DocumentUpload(BaseModel):
    filename: str
    file: UploadFile

class DocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime
    
    class Config:
        from_attributes = True