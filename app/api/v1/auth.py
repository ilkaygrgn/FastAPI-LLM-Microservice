from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserLogin, UserRead, UserCreate
from app.services.user_service import create_user, authenticate_user
from app.core.security import create_access_token
from app.models.user import User 

router = APIRouter()

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    new_user = create_user(db, user_data)
    return new_user

@router.get("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login and return JWT token"""
    authenticated = authenticate_user(db, user.email, user.password)
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    access_token = create_access_token(data={"sub": authenticated.email})
    return {"access_token": access_token, "token_type": "bearer", "user_email": authenticated.email}



@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"health_status": "ok"}