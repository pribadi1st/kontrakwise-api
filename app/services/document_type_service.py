from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from app.migrations.document_type import DocumentType as DocumentTypeModel
from app.core.db import get_db
from app.models.document_types import DocumentTypeResponse

class DocumentTypeService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_types(self, user_id: int, skip: int = 0, limit: int = 100):
        statement = select(DocumentTypeModel.id, DocumentTypeModel.name).filter(or_(DocumentTypeModel.user_id == user_id, DocumentTypeModel.user_id == None)).offset(skip).limit(limit)
        result = self.db.execute(statement).all()
        return [DocumentTypeResponse(id=row.id, name=row.name) for row in result]
        
    def add_types(self, user_id: int, name: str):
        type = DocumentTypeModel(user_id=user_id, name=name)
        self.db.add(type)
        self.db.commit()
        return type

    def get_single_type(self, user_id: int, doc_type_id: int):
        type = self.db.query(DocumentTypeModel).filter(DocumentTypeModel.id == doc_type_id, DocumentTypeModel.user_id == user_id).first()
        if not type:
            raise HTTPException(status_code=404, detail="Document type not found")
        return type

    def delete_type(self, user_id: int, doc_type_id: int):
        type = self.db.query(DocumentTypeModel).filter(DocumentTypeModel.id == doc_type_id, DocumentTypeModel.user_id == user_id).first()
        if not type:
            raise HTTPException(status_code=404, detail="Document type not found")
        self.db.delete(type)
        self.db.commit()