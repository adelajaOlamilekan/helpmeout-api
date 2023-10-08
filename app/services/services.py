import asyncio
import glob
import json
import os
import subprocess

import nanoid
from deepgram import Deepgram
from fastapi import HTTPException
from fastapi import Request

from app.database import get_db
from app.models.video_models import Video
from app.settings import VIDEO_DIR, DEEPGRAM_API_KEY


def process_video(
    video_id: int,
    file_location: str,
    filename: str,
    username: str,
):
    """
    Process a video by compressing it and extracting a thumbnail.

    Args:
        video_id (int): The ID of the video.
        file_location (str): The location of the video file.
        filename (str): The name of the video file.

    Raises:
        HTTPException: If an error occurs.

    Returns:
        None
    """
    db = next(get_db())
    video = db.query(Video).filter(Video.id == video_id).first()

    # Generate compressed and thumbnail filenames
    audio = f"audio_{filename}.mp3"
    audio_location = os.path.join(VIDEO_DIR, username, filename, audio)
    audio_location = os.path.abspath(audio_location)
    trans = f"transcript_{filename}.json"
    transcript_location = os.path.join(VIDEO_DIR, username, filename, trans)
    transcript_location = os.path.abspath(transcript_location)
    comp = f"compressed_{filename}.mp4"
    compressed_location = os.path.join(VIDEO_DIR, username, filename, comp)
    compressed_location = os.path.abspath(compressed_location)
    thumb = f"thumbnail_{filename}.jpg"
    thumbnail_location = os.path.join(VIDEO_DIR, username, filename, thumb)
    thumbnail_location = os.path.abspath(thumbnail_location)

    try:
        extract_audio(file_location, audio_location)
        asyncio.run(
            generate_transcript(
                audio_location, transcript_location, DEEPGRAM_API_KEY
            )
        )
        compress_video(file_location, compressed_location)
        extract_thumbnail(compressed_location, thumbnail_location)
    except Exception as err:
        # Update the video status to `failed`
        video.status = "failed"
        raise HTTPException(status_code=500, detail=str(err)) from err

    # Update the video status and save the compressed and thumbnail locations
    video.transcript_location = transcript_location
    video.compressed_location = compressed_location
    video.thumbnail_location = thumbnail_location
    video.status = "completed"

    db.commit()
    db.close()


def extract_audio(input_path: str, output_path: str) -> None:
    """
    Extracts the audio from a video using ffmpeg.

    Args:
        input_path (str): The path to the input video.
        output_path (str): The path to the output audio.
    """
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-vn",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "2",
        output_path,
    ]
    subprocess.run(command, check=True)


def compress_video(input_path: str, output_path: str) -> None:
    """
    Compresses a video using ffmpeg.

    Parameters:
    - input_path: The path to the input video.
    - output_path: The path to the output video.

    Returns:
    - None

    """
    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-vcodec",
        "libx264",
        "-crf",
        "28",  # Lower values will have better quality but larger size.
        output_path,
    ]
    subprocess.run(command, check=True)


def extract_thumbnail(video_path: str, thumbnail_path: str) -> None:
    """
    Extracts a thumbnail from a video using ffmpeg.

    Parameters:
    - video_path: The path to the input video.
    - thumbnail_path: The path to the output thumbnail.

    Returns:
    - None

    """
    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-ss",
        "00:00:02.000",  # Grab a frame at the 2-second mark
        "-vframes",
        "1",
        thumbnail_path,
    ]
    subprocess.run(command, check=True)


def is_valid_video(file_location: str) -> bool:
    """
    Check if a video file is valid by inspecting its metadata.
    Args:
        file_location (str): The location of the video file.
    Returns:
        bool: True if the video is valid, False otherwise.
    """
    metadata_command = ["ffmpeg", "-i", file_location]
    result = subprocess.run(
        metadata_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    msg = "Invalid data found when processing input"
    return msg not in result.stderr


def create_directory(*args):
    """
    Create a directory or directories.
    Args:
        *args: Variable length argument list of directory paths.

    Returns:
        None
    """
    for path in args:
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)


def save_blob(
    username: str, video_id: str, blob_index: int, blob: bytes
) -> str:
    """Saves a video blob/chunk.

    Parameters:
    - username: The user associated with the blob.
    - filename: The base filename for the video.
    - blob_id: The ID for this blob, indicating its sequence.
    - blob: The video blob itself.

    Returns:
    - The path to the saved blob.
    """
    # Create the directory structure if it doesn't exist
    user_dir = os.path.join(VIDEO_DIR, username)
    temp_video_dir = os.path.join(user_dir, video_id)
    create_directory(user_dir, temp_video_dir)

    # Save the blob
    blob_filename = f"{blob_index}.mp4"
    blob_path = os.path.join(temp_video_dir, blob_filename)
    with open(blob_path, "wb") as f:
        f.write(blob)

    return blob_path


def merge_blobs(username: str, video_id: str) -> str:
    """Merges video blobs/chunks to form the complete video.

    Parameters:
    - username: The user associated with the blobs.
    - filename: The base filename for the video.

    Returns:
    - The path to the merged video.
    """
    user_dir = os.path.join(VIDEO_DIR, username)
    user_dir = os.path.abspath(user_dir)
    temp_video_dir = os.path.join(user_dir, video_id)
    temp_video_dir = os.path.abspath(temp_video_dir)

    # List all blob files and sort them by their sequence ID
    blob_files = sorted(
        glob.glob(os.path.join(temp_video_dir, "*.mp4")),
        key=lambda x: int(os.path.splitext(os.path.basename(x))[0]),
    )

    # Merge the blobs
    merged_video_path = os.path.join(temp_video_dir, f"{video_id}.mp4")
    with open(merged_video_path, "wb") as merged_file:
        for blob_file in blob_files:
            with open(blob_file, "rb") as f:
                merged_file.write(f.read())

    return merged_video_path


def generate_id():
    """
    Generate a unique ID for a video.

    Returns:
    - str: A unique ID for a video.
    """

    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return str(nanoid.generate(size=10, alphabet=alphabet))


def get_transcript(audio_file: str, output_path: str) -> None:
    """
    Generate a transcript for an audio file using Deepgram's API.

    Args:
        audio_file (str): The path to the audio file.
        output_path (str): The path to the output transcript file.
    """
    # Call the async function
    asyncio.run(generate_transcript(audio_file, output_path, DEEPGRAM_API_KEY))


async def generate_transcript(audio_file: str, save_to: str, api_key: str):
    """
    Generate a transcript for an audio file using Deepgram's API.

    Args:
        audio_file (str): The path to the audio file.
        save_to (str): The path to the output transcript file.
        api_key (str): The Deepgram API key.
    """
    dg_client = Deepgram(api_key)

    params = {"punctuate": True, "tier": "enhanced"}
    with open(audio_file, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/mp3"}

        response = await dg_client.transcription.prerecorded(
            source, params, timeout=120
        )

        # Write the response to a file
        with open(save_to, "w", encoding="utf-8") as audio:
            json.dump(response, audio)


def is_logged_in(request: Request) -> bool:
    """
     Checks if a user is currently logged in.

    Parameters:
        request: Holds the request metadata of a user when interacting with
            the app.

    Returns:
        A truthy of Falsy value indicating if user is currently logged in or
            not.
    """
    return "username" in request.session and "logged_in" in request.session
