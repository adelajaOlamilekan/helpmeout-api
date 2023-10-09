""" Video routes for the FastAPI application. """
import base64
import json
import os

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_models import User
from app.services.services import is_logged_in
from app.models.video_models import Video, VideoBlob
from app.models.user_models import LogoutResponse
from app.services.services import (
    save_blob,
    merge_blobs,
    generate_id,
    process_video,
)

router = APIRouter(prefix="/srce/api")


@router.post("/start-recording/")
def start_recording(
    username: str,
    db: Session = Depends(get_db),
):
    """
    Start the recording process.

    Args:
        username (str): The username of the user.
        db (Session, optional): The database session. Default
            Depends(get_db).

    Returns:
        dict: A dictionary containing the success message and video ID.

    Raises:
        None
    """

    # Check if the user exists
    if not db.query(User).filter(User.username == username).first():
        new_user = User(username=username, hashed_password="asdfghjk")

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    video_data = Video(
        id=generate_id(),
        username=username,
    )

    db.add(video_data)
    db.commit()

    return {
        "message": "Recording started successfully",
        "video_id": video_data.id,
    }


@router.post("/upload-blob/")
def upload_video_blob(
    background_tasks: BackgroundTasks,
    request: Request,
    video_data: VideoBlob,
    db: Session = Depends(get_db),
):
    """
    Uploads a video blob to the server.

    Args:
        background_tasks (BackgroundTasks): The background tasks object.
        video_data (VideoBlob): The json data containing video information
        Db (Session, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        dict: A dictionary containing the success message and video data
            if applicable.

    Raises:
        None
    """
    # Query the database for the video id
    video = db.query(Video).filter(Video.id == video_data.video_id).first()

    # If the user is not found, raise an exception
    user = db.query(User).filter(User.username == video_data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # If the video is not found, raise an exception
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    # Decode the blob data
    blob_data = base64.b64decode(video_data.blob_object)

    # Save the blob
    _ = save_blob(
        video_data.username,
        video_data.video_id,
        video_data.blob_index,
        blob_data,
    )

    # If it's the last blob, merge all blobs and process the video
    if video_data.is_last:
        # Merge the blobs
        video.original_location = merge_blobs(
            video_data.username, video_data.video_id
        )

        video.status = "completed"
        db.commit()

        # Process the video in the background
        background_tasks.add_task(
            process_video,
            video_data.video_id,
            video.original_location,
            video_data.username,
        )

        vid_url = request.url_for("stream_video", video_id=video_data.video_id)
        response = {
            "message": "Blobs received successfully, video is being processed",
            "video_id": video_data.video_id,
            "_url": str(vid_url),
        }
        db.close()
        return json.dumps(response, indent=2)

    db.close()

    return {"msg": "Chunk received successfully!"}


@router.get("/recording/user/{username}")
def get_videos(username: str, request: Request, db: Session = Depends(get_db)):
    """
    Returns a list of videos associated with the given username.

    Parameters:
        request: The request object
        username (str): The username for which to retrieve the videos.
        request (Request): The FastAPI request object.
        db (Session): The database session.

    Returns:
        List[Video]: A list of Video objects associated with the given
            username, with downloadable URLs instead of absolute paths.
    """
    if not is_logged_in(request):
         return LogoutResponse(status_code=401, message="User not logged in")
    
    videos = db.query(Video).filter(Video.username == username).all()
    db.close()

    # Replace the absolute paths with downloadable URLs
    for video in videos:
        video_id = video.id
        video.original_location = str(request.url_for(
            "stream_video", video_id=video_id
        ))
        video.thumbnail_location = str(request.url_for(
            "get_thumbnail", video_id=video_id
        ))
        video.transcript_location = str(request.url_for(
            "get_transcript", video_id=video_id
        ))

    return videos


@router.get("/recording/{video_id}")
def stream_video(video_id: str, db: Session = Depends(get_db)):
    """
    Stream a video by its video ID.

    Parameters:
        video_id (int): The ID of the video to be streamed.
        db (Session, optional): The database session. Defaults to the
            result of the get_db function.

    Returns:
        FileResponse: The file response containing the video stream.

    Raises:
        HTTPException: If the video is not found.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    db.close()

    if video:
        return FileResponse(video.original_location, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found.")


@router.get("/recording/transcript/{video_id}")
def get_transcript(video_id: str, db: Session = Depends(get_db)):
    """
    Get the transcript for a video by its video ID.

    Parameters:
        video_id (int): The ID of the video to be streamed.
        db (Session, optional): The database session. Defaults to the
            result of the get_db function.

    Returns:
        FileResponse: The file response containing the video stream.

    Raises:
        HTTPException: If the video is not found.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    db.close()

    if video:
        return FileResponse(video.transcript_location, media_type="text/plain")
    raise HTTPException(status_code=404, detail="Video not found.")


@router.get("/recording/thumbnail/{video_id}")
def get_thumbnail(video_id: str, db: Session = Depends(get_db)):
    """
    Get the thumbnail for a video by its video ID.

    Parameters:
        video_id (int): The ID of the video to be streamed.
        db (Session, optional): The database session. Defaults to the
            result of the get_db function.

    Returns:
        FileResponse: The file response containing the video stream.

    Raises:
        HTTPException: If the video is not found.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    db.close()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")
    return FileResponse(video.thumbnail_location, media_type="image/jpeg")


@router.delete("/video/{video_id}")
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """
    Deletes a video from the database and removes its associated files
    from the file system.

    Parameters:
        video_id (int): The ID of the video to be deleted.
        db (Session, optional): The database session.
            Defaults to the result of the `get_db` function.

    Returns:
        dict: A dictionary with a single key "msg" and the value "Video
            deleted successfully!"

    Raises:
        HTTPException: If the video with the specified ID is not found
            in the database.
    """
    if video := db.query(Video).filter(Video.id == video_id).first():
        os.remove(video.original_location)
        if os.path.exists(video.thumbnail_location):
            os.remove(video.thumbnail_location)
        if os.path.exists(video.compressed_location):
            os.remove(video.compressed_location)

        db.delete(video)
        db.commit()
        db.close()

        return {"msg": "Video deleted successfully!"}

    db.close()
    raise HTTPException(status_code=404, detail="Video not found.")
