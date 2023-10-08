import base64
import json
import requests

# Configuration
VIDEO_FILE_PATH = "/home/cofucan/Videos/test_rec.mkv"
GET_VIDIO_ID_URL = "http://127.0.0.1:8000/srce/api/start-recording/"
ENDPOINT_URL = "http://127.0.0.1:8000/srce/api/upload-blob/"
BLOB_SIZE = 1 * 1024 * 1024  # 1MB by default. Adjust as needed.
USERNAME = "cofucan"
FILENAME = "videoA"  # This should be unique for each video.


def get_video_id(username: str) -> str:
    """
    Get the video ID for a user.

    Args:
        username (str): The username

    Returns:
        str: Th video id
    """
    data = {"username": username}

    headers = {"Content-Type": "application/json"}
    response = requests.post(
        GET_VIDIO_ID_URL, json=data, headers=headers, timeout=200
    )
    print(response.text)
    res_data = json.loads(response.text)
    # res_data = eval(res_data)
    print(f"Video_id: {res_data['video_id']}")
    return res_data["video_id"]


def send_blob(video_id: str, blob: bytes, blob_id: int, is_last: bool):
    """
    Sends the video in blobs

    Args:
        video_id (str): The id of the video
        blob (bytes): The blob in bytes
        blob_id (int): The index of the blob
        is_last (bool): Whether the blob is the last one
    """
    data = {
        "username": USERNAME,
        "video_id": video_id,
        "blob_index": blob_id,
        "blob_object": base64.b64encode(blob).decode("utf-8"),
        "is_last": str(is_last),
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        ENDPOINT_URL, json=data, headers=headers, timeout=200
    )
    print(response.text)


def main():
    """ The main function """
    video_id = get_video_id("user10")
    with open(VIDEO_FILE_PATH, "rb") as f:
        blob_id = 1
        while True:
            blob = f.read(BLOB_SIZE)
            if not blob:
                break
            is_last = len(blob) < BLOB_SIZE
            send_blob(video_id, blob, blob_id, is_last)
            blob_id += 1


if __name__ == "__main__":
    main()
