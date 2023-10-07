from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import base64
import os

from app.services.services import save_blob, merge_blobs, generate_id
from app.models.video_models import Video, VideoBlob
from app.database import get_db

router = APIRouter(prefix="/scre/api")


@router.post("/start-recording/")
def start_recording(
    video_data: VideoBlob,
    db: Session = Depends(get_db),
):
    """
    Start the recording process.
    Args:
        user_id (str): The user ID.
        db (Session, optional): The database session. Defaults to
            Depends(get_db).

    Returns:
        dict: A dictionary containing the success message and video ID.7

    Raises:
        None
    """
    user_id = video_data.user_id
    video_data = Video(
        id = generate_id(),
        user_id=user_id,
    )

    db.add(video_data)
    db.commit()

    Response = {
            "message": "Recording started successfully",
            "video_id": video_data.id,
        }

    return json.dumps(Response, indent = 2)


@router.post("/recording/{video_id}")
def upload_video_blob(
    background_tasks: BackgroundTasks,
    video_id: str,
    video_data: VideoBlob,
    db: Session = Depends(get_db),
):
    """
    Uploads a video blob to the server.

    Args:
        background_tasks (BackgroundTasks): The background tasks object.
        video_blob (VideoBlob): The video blob data.
        db (Session, optional): The database session. Defaults to
            Depends(get_db).

    Returns:
        dict: A dictionary containing the success message and video data if
            applicable.

    Raises:
        None
    """
    # Query the database for the video id
    video = db.query(Video).filter(Video.id == video_id).first()

    # If the video is not found, raise an exception
    if not video:
        raise HTTPException(status_code=404, detail="Video not found.")

    # Decode the blob data
    blob_data = base64.b64decode(video_data.blob_object)

    # Save the blob
    _ = save_blob(video_data.user_id, video_id, video_data.blob_index, blob_data)

    # If it's the last blob, merge all blobs and process the video
    if video_blob.is_last:
        # Update the video status to processing
        video_data.status = "processing"
        db.commit()
        db.close

        # Merge the blobs in a background task
        background_tasks.add_task(
            merge_blobs,
            video_data.user_id,
            video_id
        )

        # Process the video in the background
        # background_tasks.add_task(
        #     process_video,
        #     video_data.id,
        #     merged_video_path,
        #     video_blob.filename,
        # )
        
        Response = {
            "message": "Chunks received successfully and video is being processed",
            "video_id": video_id,
            "video_url": f"/scre/api/recording/{video_data.video_id}",
            "thumbnail_url": f"/scre/api/thumbnail/{video_data.video_id}",
            "transcript_url": f"/scre/api/transcript/{video_data.video_id}",
        }
        return json.dumps(Response, indent = 2)
    db.close()

    return {"msg": "Video blob received successfully!"}


@router.get("/videos/user/{user_id}")
def get_videos(user_id: str, db: Session = Depends(get_db)):
    """
    Returns a list of videos associated with the given uswr_id.
    Parameters:
        username (str): The username for which to retrieve the videos.
        db (Session): The database session.
    Returns:
        List[Video]: A list of Video objects associated with the given
            username.
    """
    videos = db.query(Video).filter(Video.user_id == user_id).all()
    db.close()
    return json.dumps(videos, indent = 2)


@router.get("/video/{video_id}")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    """
    Stream a video by its video ID.
    Parameters:
    - video_id (int): The ID of the video to be streamed.
    - db (Session, optional): The database session. Defaults to the result of
        the get_db function.
    Returns:
    - FileResponse: The file response containing the video stream.
    Raises:
    - HTTPException: If the video is not found.
    """
    video = db.query(Video).filter(Video.id == video_id).first()
    db.close()

    if video:
        return FileResponse(video.original_location, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video not found.")


@router.delete("/video/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """
    Deletes a video from the database and removes its associated files from the
        file system.

    Parameters:
        - video_id (int): The ID of the video to be deleted.
        - db (Session, optional): The database session. Defaults to the result
            of the `get_db` function.

    Returns:
        - dict: A dictionary with a single key "msg" and the value "Video
            deleted successfully!"

    Raises:
        - HTTPException: If the video with the specified ID is not found in
            the database.
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
