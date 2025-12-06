# app/schemas/user.py
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password length - bcrypt has a 72-byte limit"""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError(
                f"Password is too long. Maximum length is 72 bytes "
                f"({len(password_bytes)} bytes provided). Please use a shorter password."
            )
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password length - bcrypt has a 72-byte limit"""
        password_bytes = v.encode('utf-8')
        if len(password_bytes) > 72:
            raise ValueError(
                f"Password is too long. Maximum length is 72 bytes "
                f"({len(password_bytes)} bytes provided). Please use a shorter password."
            )
        return v

class UserRead(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True