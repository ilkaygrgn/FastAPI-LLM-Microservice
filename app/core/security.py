import bcrypt
from passlib.context import CryptContext
from app.core.config import settings
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from typing import Optional
from app.db.session import get_db 
from app.models.user import User
from sqlalchemy.orm import Session


# Define the OAuth2 scheme (where FastAPI looks for the token: Authorization: Bearer <token>)
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme = HTTPBearer()
# Keep passlib context for backward compatibility with existing hashes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Note: Password length validation should be done at the schema level.
    Bcrypt has a 72-byte limit, but we rely on Pydantic validation to enforce this.
    This function includes a safety check as a last resort.
    """
    # Safety check: ensure password is within bcrypt's 72-byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError(
            f"Password exceeds bcrypt's 72-byte limit: {len(password_bytes)} bytes. "
            "This should have been caught by schema validation."
        )
    try:
        # Use bcrypt directly to avoid passlib issues
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except ValueError as e:
        # Re-raise with more context if it's a length-related error
        if "72" in str(e) or "byte" in str(e).lower():
            raise ValueError(
                f"Password hashing failed: {e}. "
                f"Password length: {len(password_bytes)} bytes. "
                f"Password (first 20 chars): {password[:20]}"
            ) from e
        raise

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Note: Password length validation should be done at the schema level.
    This function includes a safety check as a last resort.
    Supports both direct bcrypt hashes and passlib-formatted hashes for backward compatibility.
    """
    # Safety check: ensure password is within bcrypt's 72-byte limit
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        raise ValueError(
            f"Password exceeds bcrypt's 72-byte limit: {len(password_bytes)} bytes. "
            "This should have been caught by schema validation."
        )
    try:
        # Try bcrypt directly first (for new hashes)
        try:
            return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
        except (ValueError, TypeError):
            # Fall back to passlib for backward compatibility with existing hashes
            return pwd_context.verify(plain_password, hashed_password)
    except ValueError as e:
        # Re-raise with more context if it's a length-related error
        if "72" in str(e) or "byte" in str(e).lower():
            raise ValueError(
                f"Password verification failed: {e}. "
                f"Password length: {len(password_bytes)} bytes. "
                f"Password (first 20 chars): {plain_password[:20]}"
            ) from e
        raise

def create_access_token(data: dict, expires_delta: int = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_delta or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.REFRESH_SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Decodes the access token and returns the subject (user email)."""
    try:
        # 1. Decode the JWT payload
        payload = jwt.decode(
            token,
            settings.SECRET_KEY, # Use the main SECRET_KEY for access tokens
            algorithms=[settings.ALGORITHM]
        )
        # 2. Extract the subject (email)
        email: str = payload.get("sub")
        # --- TEMPORARY LOGGING ---
        print(f"DEBUG: Token decoded successfully. Email found: {email}")
        # --- END TEMPORARY LOGGING ---
        if not email:
            # --- TEMPORARY LOGGING ---
            print("DEBUG: Token decoded, but 'sub' (email) claim is missing.")
            # --- END TEMPORARY LOGGING ---
            return None
        
        # 3. Check token expiration (optional, JOSE handles this by default but good for clarity)
        # expiration = payload.get("exp")
        # if datetime.fromtimestamp(expiration) < datetime.utcnow():
        #     raise JWTError("Token expired")

        return email
        
    except JWTError as e:
        # Handle all other JWT errors (invalid signature, claims, etc.)
        # print(f"JWT Decode Error: {e}") # For debugging
        # --- TEMPORARY LOGGING ---
        print(f"DEBUG: JWT Decode FAILED! Error: {e}") 
        # --- END TEMPORARY LOGGING ---
        return None # Return None on failure


async def get_current_user(
    db: Session = Depends(get_db),
    #token: str = Depends(oauth2_scheme)
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
):
    """
    Dependency function to get the current user from the token.
    Raises 401 UNAUTHORIZED if the token is invalid or user not found.
    """

    # Extract the actual token string
    token_str = token.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Use the utility to get the user email
    email = decode_access_token(token_str)
    
    if email is None:
        raise credentials_exception
    
    # Look up the user in the database
    user = db.query(User).filter(User.email == email).first()
    
    if user is None:
        raise credentials_exception
        
    return user

# def get_current_active_user(current_user: User = Depends(get_current_user)):
#     """
#     Dependency function to ensure the user is active (can be extended).
#     """
#     # You can add logic here to check user.is_active or user.is_disabled
#     # For now, we'll assume any found user is active.
#     # if not current_user.is_active:
#     #     raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user