from datetime import datetime, timezone
from typing import Optional, Union

from fastapi import UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, Enum, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, index = True, unique=True, nullable=False)
    password: str = Column(String, nullable=False)
    email: str = Column(String, nullable=False)
    created_date: DateTime = Column(DateTime, server_default=func.now())
    updated_date: DateTime = Column(DateTime, onupdate=func.now())
    is_deleted: bool = Column(Boolean, default= False)

class UserSchema(BaseModel):
    email: str
    password: str
    id: Optional[int]= None
    username: Optional[str] = None