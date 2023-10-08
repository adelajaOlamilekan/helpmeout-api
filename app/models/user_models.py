from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(
        String, index=True, unique=True, nullable=False, default=None
    )
    hashed_password: str = Column(String, unique=True, nullable=False)
    created_date: DateTime = Column(DateTime, server_default=func.now())
    updated_date: DateTime = Column(DateTime, onupdate=func.now())
    is_deleted: bool = Column(Boolean, default=False)


class UserRequest(BaseModel):
    username: str


class UserAuthentication(UserRequest):
    password: str


class UserResponse(BaseModel):
    message: str
    status_code: int
    data: Optional[dict] = None


class LogoutResponse(BaseModel):
    message: str
    status_code: int
