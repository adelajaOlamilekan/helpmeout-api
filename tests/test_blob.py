import base64

import requests

# Configuration
VIDEO_FILE_PATH = "/home/destinedcodes/video.mp4"
START_URL = "http://127.0.0.1:8000/srce/api/start-recording/"
UPLOAD_URL = "http://127.0.0.1:8000/srce/api/upload-recording/"
BLOB_SIZE = 1 * 1024 * 1024  # 1MB by default. Adjust as needed.
USER_ID = "cofucan"
FILENAME = "videoA"  # This should be unique for each video.


def start_record(user_id):
    data = {
        "user_id": user_id,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(START_URL, json=data, headers=headers)
    # Check if the response is in JSON format
    if response.status_code == 200:
        response_data = response.json()
        video_id = response_data.get("video_id")
        if video_id:
            return video_id
        else:
            print("Video ID not found in the response.")
    else:
        print(f"Request failed with status code: {response.status_code}")

def send_blob(video_id, blob, blob_index, is_last):
    data = {
        "blob_index": int(blob_index),
        "user_id": USER_ID,
        "video_id": video_id,
        "blob_object": base64.b64encode(blob).decode("utf-8"),
        "is_last": str(is_last),
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(UPLOAD_URL, json=data, headers=headers)
    print(response.text)


def main():
    with open(VIDEO_FILE_PATH, "rb") as f:
        blob_id = 1
        while True:
            blob = f.read(BLOB_SIZE)
            if not blob:
                break
            is_last = len(blob) < BLOB_SIZE
            video_id = start_record(USER_ID)
            send_blob(video_id, blob, blob_id, is_last)
            blob_id += 1


if __name__ == "__main__":
    main()
