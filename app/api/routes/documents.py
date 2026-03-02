from typing import Annotated
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from app.core.db import get_db
from sqlalchemy.orm import Session
from app.migrations.users import User as UserModel
from app.api.guards import get_current_user
from app.services.documents_service import DocumentService
from app.services.ai_analysis_service import AIAnalysisService
from app.models.documents import DocumentDetailResponse
from app.models.ai_analysis import AIAnalysisDTO, AIListRules

router = APIRouter()

def init_document_service(db: Session = Depends(get_db)):
    return DocumentService(db)

def init_ai_analysis_service(db: Session = Depends(get_db)):
    return AIAnalysisService(db)

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
    document_type_id: int = Form(...),
    document_service: DocumentService = Depends(init_document_service),
):
    await document_service.upload_document(current_user.id, file, filename, document_type_id)
    return {"detail": "success"}

@router.get("/{document_id}/file", response_model=DocumentDetailResponse)
def get_document(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    document_id: int,
    document_service: DocumentService = Depends(init_document_service)
):
    doc = document_service.get_document_detail(current_user.id, document_id)
    return doc

@router.get("/{document_id}/download")
def get_document(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    document_id: int,
    document_service: DocumentService = Depends(init_document_service)
):
    doc = document_service.get_document_detail(current_user.id, document_id)
    path = f"./{doc.file_path}"
    return FileResponse(path=path, media_type="application/pdf", filename=doc.filename)

@router.get("/{document_id}/sync")
async def sync_document(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    document_id: int,
    document_service: DocumentService = Depends(init_document_service)
):
    await document_service.sync_document(current_user.id, document_id)
    return {"detail": "success"}

@router.delete("/{document_id}")
def delete_document(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    document_id: int,
    document_service: DocumentService = Depends(init_document_service)
):
    document_service.delete_document(current_user.id, document_id)
    return {"detail": "success"}

@router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    analysis_dto: AIAnalysisDTO,
    document_service: DocumentService = Depends(init_document_service),
    ai_service: AIAnalysisService = Depends(init_ai_analysis_service),
):
    """Analyze a document using AI"""
    try:
        # Verify document exists and belongs to user
        document = document_service.get_document_detail(current_user.id, document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document Not Found")
        
        # Execute analysis
        result = await ai_service.analyze_document(current_user.id, analysis_dto, document)
        # return result
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

