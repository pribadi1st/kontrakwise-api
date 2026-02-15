from pydantic import BaseModel


class DocumentTypeResponse(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class DocumentCreateModel(BaseModel):
    name: str