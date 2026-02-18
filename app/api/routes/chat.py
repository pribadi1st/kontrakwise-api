from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.chat import ChatRequest
# from app.services.chat import ChatService
from app.api.guards import get_current_user
from app.services.chat_service import ChatService
from app.core.db import get_db

router = APIRouter()

def init_chat_service(db: Session = Depends(get_db)):
    return ChatService(db)

@router.post("/query")
def chat_with_docs(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    chat_service: ChatService = Depends(init_chat_service)
):
    result = chat_service.generate_response_for_single_doc(current_user.id, request)
    return result

@router.post("/query-stream")
def chat_with_docs_stream(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    chat_service: ChatService = Depends(init_chat_service)
):
    """Streaming chat endpoint using Server-Sent Events"""
    def generate():
        try:
            yield from chat_service.generate_response_for_single_doc_stream(current_user.id, request)
        except Exception as e:
            # Ensure error is also sent as SSE
            import json
            yield f"data: {json.dumps({'type': 'error', 'message': f'Streaming error: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )