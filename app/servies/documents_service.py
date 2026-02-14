import shutil
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile
from app.migrations.documents import Document as DocumentModel
from pathlib import Path
import pymupdf

from app.core.db import get_db
from app.core.embedding_client import embedding_client
from app.core.pinecone_client import pinecone_client
from app.models.documents import DocumentResponse
from sqlalchemy import select
from fastapi import HTTPException

class DocumentService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.upload_path = Path("./storage")

    def get_documents(self, user_id: int, skip: int = 0, limit: int = 100):
        stmt = select(DocumentModel.id, DocumentModel.filename, DocumentModel.created_at).filter(
            DocumentModel.user_id == user_id
        ).limit(limit).offset(skip)
        result = self.db.execute(stmt).all()
        return [DocumentResponse(id=row.id, filename=row.filename, created_at=row.created_at) for row in result]

    def get_document_detail(self, user_id: int, document_id: int):
        doc = self.db.query(DocumentModel).filter(
            DocumentModel.user_id == user_id,
            DocumentModel.id == document_id
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    async def upload_document(self, user_id: int, file: UploadFile, filename: str):
        db_document = DocumentModel(
            user_id=user_id, 
            filename=filename, 
            file_path="temp" # Placeholder
        )
        self.db.add(db_document)
        self.db.flush()
        new_id = db_document.id
        doc_path = self.upload_path / str(user_id)
        doc_path.mkdir(parents=True, exist_ok=True)
        path = doc_path / f"{new_id}_{filename}.{file.filename.split('.')[-1]}"
        try:
            with path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            file.file.close()
        db_document.file_path = str(path)
        self.db.commit()
        self.db.refresh(db_document)
        self.upload_to_pinecone(str(path), db_document.id, user_id)
        return db_document
    
    def upload_to_pinecone(self, path: str, document_id: int, user_id: int):
        text = ""
        doc = pymupdf.open(path)
        for page in doc:
            text += page.get_text()
        
        # Create embedding
        embedding = embedding_client.create_embedding(text)
        
        # Prepare vector for Pinecone
        vector_id = f"doc_{document_id}"
        vector_data = {
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "document_id": document_id,
                "user_id": user_id,
                "file_path": path,
                "text_preview": text[:500]  # First 500 chars for preview
            }
        }
        
        # Upload to Pinecone
        pinecone_client.upsert_vectors([vector_data])
        
        
        