from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str  
    document_id: int | None = None
    role: Optional[str] = 'user'