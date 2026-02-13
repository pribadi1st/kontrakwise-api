from fastapi import UploadFile
from pydantic import BaseModel

class DocumentUpload(BaseModel):
    filename: str
    file: UploadFile