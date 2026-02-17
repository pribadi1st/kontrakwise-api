import shutil
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile
from app.migrations.documents import Document as DocumentModel
from pathlib import Path
import pymupdf

from app.core.db import get_db
from app.core.gemini_client import gemAI
from app.core.pinecone_client import pinecone_client
from app.models.documents import DocumentResponse
from sqlalchemy import select
from fastapi import HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument
from app.services.document_type_service import DocumentTypeService


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

    async def upload_document(self, user_id: int, file: UploadFile, filename: str, document_type_id: int):
        document_type_service = DocumentTypeService(self.db)
        document_type = document_type_service.get_single_type(user_id, document_type_id)
        if not document_type:
            raise HTTPException(status_code=404, detail="Document type not found")

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
        doc = pymupdf.open(path)
        namespace = f"user_{user_id}"
        
        raw_documents = []
        for page in doc:
            # Create a tiny object for each page that knows its page number
            raw_documents.append(
                LCDocument(
                    page_content=page.get_text(),
                    metadata={"page": page.number + 1} # PyMuPDF .number is 0-indexed
                )
            )
        
        # 2. Smart Chunking (this will now preserve the metadata!)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " "]
        )
        
        # .split_documents is smarter than .split_text
        # If a chunk comes from Page 1, it keeps {"page": 1} in its metadata
        chunks = text_splitter.split_documents(raw_documents)
        
        # 2. Prepare Vectors in a List (Batching)
        vectors_to_upsert = []
        
        for i, chunk in enumerate(chunks):
            embedding = gemAI.create_embedding(chunk.page_content)
            
            vectors_to_upsert.append({
                "id": f"doc_{document_id}_chunk_{i}",
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "user_id": user_id,
                    "text": chunk.page_content, # The actual text
                    "page": chunk.metadata["page"], # <--- THE PAGE NUMBER LIVES!
                    "chunk_index": i
                }
            })
        
        # 3. Single Batch Upload (Much Faster)
        # Pinecone handles up to 100-200 vectors per call comfortably
        pinecone_client.upsert_vectors(vectors_to_upsert, namespace=namespace)
        
        