import asyncio
import glob
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
    video_id: str,
    file_location: str,
    username: str,
):
    """
    Process a video by compressing it and extracting a thumbnail.

    Args:
        video_id (str): The ID of the video.
        file_location (str): The location of the video file.
        username (str): The name of the user.

    Raises:
        HTTPException: If an error occurs.

    Returns:
        None
    """

    # Get a database connection
    db = next(get_db())

    # Query the video by ID
    video = db.query(Video).filter(Video.id == video_id).first()

    # Generate file paths for audio, transcript, compressed video, and thumbnail
    audio_filename = f"audio_{video_id}.mp3"
    audio_location = os.path.abspath(
        os.path.join(VIDEO_DIR, username, video_id, audio_filename)
    )

    transcript_filename = f"transcript_{video_id}.srt"
    transcript_location = os.path.abspath(
        os.path.join(VIDEO_DIR, username, video_id, transcript_filename)
    )

    compressed_filename = f"compressed_{video_id}.mp4"
    compressed_location = os.path.abspath(
        os.path.join(VIDEO_DIR, username, video_id, compressed_filename)
    )

    thumbnail_filename = f"thumbnail_{video_id}.jpg"
    thumbnail_location = os.path.abspath(
        os.path.join(VIDEO_DIR, username, video_id, thumbnail_filename)
    )

    try:
        # Extract audio from the video
        extract_audio(file_location, audio_location)

        # Generate transcript using external API
        asyncio.run(
            generate_transcript(
                audio_location, transcript_location, DEEPGRAM_API_KEY
            )
        )

        # Compress the video
        # compress_video(file_location, compressed_location)

        # Extract thumbnail from compressed video
        # extract_thumbnail(compressed_location, thumbnail_location)

    except Exception as err:
        # Update the video status to `failed` if an error occurs
        video.status = "failed"
        raise HTTPException(status_code=500, detail=str(err)) from err

    # Update the video status and save the transcript location
    video.transcript_location = transcript_location
    # video.compressed_location = compressed_location
    # video.thumbnail_location = thumbnail_location
    video.status = "completed"

    # Commit changes to the database and close the connection
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
        "-b:a",
        "12k",
        output_path,
    ]
    subprocess.run(command, check=True)


def compress_video(input_path: str, output_path: str) -> None:
    """
    Compresses a video using ffmpeg.

    Args:
        input_path: The path to the input video.
        output_path: The path to the output video.

    Returns:
        None

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

    Args:
        video_path: The path to the input video.
        thumbnail_path: The path to the output thumbnail.

    Returns:
        None

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
    """
    Saves a video blob/chunk.

    Args:
        username: The user associated with the blob.
        video_id: The ID of the video associated with the blob.
        blob_index: The index of the blob.
        blob: The video blob itself.

    Returns:
        The path to the saved blob.
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
    """
    Merges video blobs/chunks to form the complete video.

    Args:
        username: The user associated with the blobs.
        video_id: The ID of the video associated with the blobs.

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
        str: A unique ID for a video.
    """

    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return str(nanoid.generate(size=15, alphabet=alphabet))


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
    deepgram = Deepgram(api_key)

    params = {"punctuate": True, "tier": "enhanced", "utterances": True}
    # params = {'smart_format': True, 'utterances': True}
    with open(audio_file, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/mp3"}

        response: dict = deepgram.transcription.sync_prerecorded(
            source, params
        )
        # response = deepgram.extra.to_WebVTT(response)
        deepgram.extra.to_SRT(response)
        # response.to_SRT()

        convert_to_srt(response, save_to)


def convert_to_srt(transcript_data: dict, output_path: str) -> None:
    """
    Convert a transcript to SRT format.

    Args:
        transcript_data (dict): The transcript data.
        output_path (str): The path to the output SRT file.

    Returns:
        None
    """
    data = transcript_data

    # Extract transcript and word-level information
    _ = data["results"]["channels"][0]["alternatives"][0]["transcript"]
    words = data["results"]["channels"][0]["alternatives"][0]["words"]

    # Create SRT caption file
    srt_file = []

    for i, word_info in enumerate(words):
        start_time = round(word_info["start"], 3)
        end_time = round(word_info["end"], 3)
        word_text = word_info["punctuated_word"]

        srt_entry = f"{i + 1}\n{start_time} --> {end_time}\n{word_text}\n"
        srt_file.append(srt_entry)

    # Save SRT caption file
    with open(output_path, "w", encoding="utf-8") as file:
        file.writelines(srt_file)


def is_logged_in(request: Request) -> bool:
    """
     Checks if a user is currently logged in.

    Args:
        request: The request object.

    Returns:
        bool: True if the user is logged in, False otherwise.
    """
    return "username" in request.session and "logged_in" in request.session
