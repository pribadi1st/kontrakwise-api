from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.core.security import get_password_hash
from app.models.users import User, UserRegisterModel, UserLoginModel
from app.core.db import get_db
from app.migrations.users import User as UserModel
from app.core.security import verify_password
from datetime import timedelta
from app.core.config import settings
from app.core.security import create_access_token

class UserService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    def get_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        return self.db.query(UserModel).limit(limit).offset(offset).all()

    def register(self, user_in: UserRegisterModel):
        user_exists = self.db.query(UserModel).filter(UserModel.email == user_in.email).first()
        if user_exists:
            raise HTTPException(status_code=409, detail="User already exists")
        
        try:
            hashed_pw = get_password_hash(user_in.password)
            db_user = UserModel(email=user_in.email, hashed_password=hashed_pw)
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        return "success"

    def login(self, user_in: UserLoginModel):
        user = self.db.query(UserModel).filter(UserModel.email == user_in.email).first()
        if not user or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.EXPIRE_JWT_KEY)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        return {"access_token": access_token}