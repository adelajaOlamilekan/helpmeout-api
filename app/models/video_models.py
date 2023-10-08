from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Enum, String, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id: str = Column(String, primary_key=True, unique=True, nullable=False)
    user_id: int = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # user_id: str = Column(String, nullable=True)
    created_date: DateTime = Column(DateTime, default=datetime.utcnow)
    original_location: str = Column(String, nullable=True)
    compressed_location: str = Column(String, nullable=True)
    thumbnail_location: str = Column(String, nullable=True)
    transcript_location: str = Column(String, nullable=True)
    status: str = Column(
        Enum(
            "processing",
            "completed",
            "failed",
            name="processing_status",
        ),
        default="processing",
    )

    user = relationship("User", backref="videos")


class VideoBlob(BaseModel):
    user_id: int
    video_id: str
    blob_index: int
    blob_object: bytes
    is_last: bool
