from sqlalchemy.orm import Session
from app.db.models import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user"""
    hashed_pw = hash_password(user_data.password)
    db_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    "Return a user if the email and password are correct"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user