from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, Depends
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.migrations.users import User as UserModel
from app.api.guards import get_current_user
from app.models.documents import DocumentUpload
from app.servies.documents_service import DocumentService

router = APIRouter()

def init_document_service(db: Session = Depends(get_db)):
    return DocumentService(db)

@router.get("/")
def get_documents(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0, 
    limit: int = 10, 
    document_service: DocumentService = Depends(init_document_service)
):
    documents = document_service.get_documents(current_user.id, skip, limit)
    return documents

@router.post("/upload")
async def upload_document(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    file: UploadFile = File(...),
    filename: str = Form(...),
    document_service: DocumentService = Depends(init_document_service),
):
    await document_service.upload_document(current_user.id, file, filename)
    return {"detail": "success"}