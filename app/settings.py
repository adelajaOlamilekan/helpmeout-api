""" This file contains all the settings for the application. """
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

DEEPGRAM_API_KEY= ""
#config["deepgram"]["api_key"]


DB_USER = "fastapi_user"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "helpmeout"
DB_TYPE = "sqlite"
MEDIA_DIR = "./media"
VIDEO_DIR = f"{MEDIA_DIR}/uploads/"
COMPRESSED_DIR = f"{MEDIA_DIR}/compressed/"
THUMBNAIL_DIR = f"{MEDIA_DIR}/thumbnails/"
GOOGLE_CLIENT_ID="132857240334-rru04m8on4l5m8s1st03h2v8s3vb6ub4.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="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"
FACEBOOK_CLIENT_ID="993445638551349"
FACEBOOK_CLIENT_SECRET="1a5ed4c06de502b99ee1a29deb9c19a8"
SESSION_COOKIE_NAME="server"
