""" The video models """""
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Enum, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Video(Base):
    """ The video model """
    __tablename__ = "videos"

    id: str = Column(String, primary_key=True, unique=True, nullable=False)
    username = Column(
        String,
        ForeignKey("users.username", ondelete="CASCADE"),
        nullable=False,
    )
    created_date = Column(DateTime, default=datetime.utcnow)
    original_location = Column(String, nullable=True)
    compressed_location = Column(String, nullable=True)
    thumbnail_location = Column(String, nullable=True)
    transcript_location = Column(String, nullable=True)
    status = Column(
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
    """ The video blob model """
    username: str
    video_id: str
    blob_index: int
    blob_object: bytes
    is_last: bool
