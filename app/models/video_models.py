from datetime import datetime, timezone
from typing import Optional, Union

from fastapi import UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, Enum, Integer, String, DateTime, ForeignKey

from user_models import User

from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, index=True)
    created_date: DateTime = Column(DateTime, default=datetime.utcnow)
    original_location: str = Column(String)
    compressed_location: str = Column(String, nullable=True)
    thumbnail_location: str = Column(String, nullable=True)
    file_type: str = Column(String)
    status: str = Column(
        Enum("pending", "complete", "failed", name="processing_status"),
        default="pending",
    )


class VideoBlob(BaseModel):
    blobId: int
    username: str
    filename: str
    blobObject: Union[bytes, UploadFile]
    is_last: bool


class VideoSchema(BaseModel):
    id: Optional[int] = None
    username: str
    created_date: Optional[datetime] = datetime.now(timezone.utc)
    original_location: str
    compressed_location: str
    thumbnail_location: str
    file_type: str
    status: Optional[str] = "pending"
