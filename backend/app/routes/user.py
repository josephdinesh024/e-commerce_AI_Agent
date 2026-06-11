from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import schemas
from app.services.user import UserService

router = APIRouter(prefix="/user", tags=["users"])

@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        return UserService(db).create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=schemas.UserLoginResponse)
def login_user(user_login: schemas.UserLogin, db: Session = Depends(get_db)):
    print(user_login)
    try:
        return UserService(db).create_user_session(user_login)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@router.put("/update", response_model=schemas.UserResponse)
def update_user(user_update: schemas.UserUpdate, session_id: str, db: Session = Depends(get_db)):
    """Update user information"""
    try:
        return UserService(db).Update_user(session_id, user_update)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@router.get("/me", response_model=schemas.UserResponse)
def get_current_user(session_id: str, db: Session = Depends(get_db)):
    """Get current user information based on session"""
    try:
        return UserService(db).get_current_user(session_id)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))