from enum import unique
from fastapi import UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, Enum, Integer, String, DateTime
from nanoid import generate
from datetime import datetime
from typing import Union
from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: str = Column(String, primary_key=True, unique=True, default=generate(size=10))
    username: str = Column(String, index=True)
    created_date: DateTime = Column(DateTime, default=datetime.utcnow)
    original_location: str = Column(String)
    compressed_location: str = Column(String, nullable=True)
    thumbnail_location: str = Column(String, nullable=True)
    file_type: str = Column(String)
    status: str = Column(
        Enum("pending", "processing" "complete", "failed", name="processing_status"),
        default="pending",
    )


class VideoBlob(BaseModel):
    video_id: str
    blob_index: int
    user_id: str
    blob_object: Union[bytes, UploadFile]
    is_last: bool
