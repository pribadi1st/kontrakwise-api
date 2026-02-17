from fastapi import APIRouter
from app.api.routes import users, documents, document_types, chat

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(document_types.router, prefix="/document-types", tags=["document-types"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])