from typing import Annotated
from fastapi import APIRouter, Depends
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.migrations.users import User as UserModel
from app.api.guards import get_current_user
from app.servies.document_type_service import DocumentTypeService
from app.models.document_types import DocumentCreateModel

router = APIRouter()

def init_document_type_service(db: Session = Depends(get_db)):
    return DocumentTypeService(db)

@router.get("/")
def get_documents(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    skip: int = 0, 
    limit: int = 10, 
    document_type_service: DocumentTypeService = Depends(init_document_type_service)
):
    documents = document_type_service.get_types(current_user.id, skip, limit)
    return documents

@router.post("/")
def add_types(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    body: DocumentCreateModel,
    document_type_service: DocumentTypeService = Depends(init_document_type_service),
):
    document_type_service.add_types(current_user.id, body.name)
    return {"detail": "success"}

@router.delete("/{id}")
def delete_types(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    id: int,
    document_type_service: DocumentTypeService = Depends(init_document_type_service),
):
    document_type_service.delete_type(current_user.id, id)
    return {"detail": "success"}