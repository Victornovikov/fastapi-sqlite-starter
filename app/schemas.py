from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============== User Schemas ==============

class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


# ============== Item Schemas ==============

class ItemCreate(BaseModel):
    """Schema for creating a new item"""
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, max_length=10000)
    is_public: bool = False


class ItemUpdate(BaseModel):
    """Schema for updating an item"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, max_length=10000)
    is_public: Optional[bool] = None


class ItemResponse(BaseModel):
    """Schema for item response"""
    id: int
    user_id: int
    title: str
    content: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    """Schema for paginated item list"""
    items: List[ItemResponse]
    total: int
    page: int
    per_page: int