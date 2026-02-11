from pydantic import BaseModel, EmailStr
from datetime import datetime

class User(BaseModel):
    id: int
    email: EmailStr
    hashed_password: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserRegisterModel(BaseModel):
    email: EmailStr
    password: str

class UserLoginModel(BaseModel):
    email: EmailStr
    password: str
    
