from fastapi import APIRouter, Depends, HTTPException, status
from jose.exceptions import JWTClaimsError, JWTError
from sqlalchemy.orm import Session
from jose import jwt
from fastapi import Body
from app.schemas.token import Token
from app.core.config import settings
from app.db.session import get_db
from app.schemas.user import UserLogin, UserRead, UserCreate
from app.services.user_service import create_user, authenticate_user
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User 

router = APIRouter()

@router.post("/register", response_model=UserRead)
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

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login and return JWT token"""
    authenticated = authenticate_user(db, user.email, user.password)
    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    # Create both access and refresh tokens
    access_token = create_access_token(data={"sub": authenticated.email})
    refresh_token = create_refresh_token(data={"sub": authenticated.email})
    
    # Store refresh token in database
    authenticated.refresh_token = refresh_token
    db.commit()
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """ON FRONTEND DELETE THE TOKEN FROM THE COOKIE!!"""
    return {"message": "Logged out successfully"}


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Body(...), db: Session = Depends(get_db)):
    """Refresh the access token"""
    try:
        payload = jwt.decode(refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    user = db.query(User).filter(User.email == email).first()
    if not user or user.refresh_token != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.email})
    new_refresh_token = create_refresh_token(data={"sub": user.email})

    #Update refresh token in database
    user.refresh_token = new_refresh_token
    db.commit()

    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}



@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"health_status": "ok"}