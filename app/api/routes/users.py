from fastapi import APIRouter, Depends, status
from app.api.guards import get_current_user
from app.models.users import User as UserResponse, UserLoginModel, UserRegisterModel, UserEmailResponse
from app.migrations.users import User as UserModel
from app.services.user_service import UserService
from app.core.db import get_db
from sqlalchemy.orm import Session
from typing import Annotated

router = APIRouter()

def init_user_service(db: Session = Depends(get_db)):
    return UserService(db)

@router.get("/", response_model=list[UserResponse])
def get_users(skip: int = 0, limit: int = 100, user_service: UserService = Depends(init_user_service)):
    users = user_service.get_users(skip, limit)
    return users

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegisterModel, user_service: UserService = Depends(init_user_service)):
    user = user_service.register(user_in)
    return { "detail":"success"}
    
@router.post("/login")
def login(
    user_in: UserLoginModel, 
    user_service: UserService = Depends(init_user_service)
):
    return user_service.login(user_in)

@router.get("/me", response_model=UserEmailResponse)
def read_users_me(current_user: Annotated[UserModel, Depends(get_current_user)]):
    return UserEmailResponse(email=current_user.email)