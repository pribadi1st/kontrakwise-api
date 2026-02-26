from pydantic import BaseModel
from typing import Optional, Literal


class DocumentTypeResponse(BaseModel):
    id: int
    name: str
    description: str
    risk_rules: Optional[list[dict]] = None
    
    class Config:
        from_attributes = True

class DocumentRiskLevel(BaseModel):
    clause: str
    severity: Literal['low', 'medium', 'high']
    criteria: str

class DocumentCreateModel(BaseModel):
    name: str
    description: str
    risk_rules: Optional[list[DocumentRiskLevel]] = None

class DocumentUpdateModel(DocumentCreateModel):
    pass
