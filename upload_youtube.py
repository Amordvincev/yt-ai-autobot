import os
import json
import pickle

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

TOKEN_DIR = os.path.join(os.path.dirname(__file__), ".yt_token")
CLIENT_SECRET_PATH = os.path.join(os.path.dirname(__file__), "client_secret.json")
TOKEN_PATH = os.path.join(TOKEN_DIR, "token.pickle")


def authenticate():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_PATH):
                print("[YouTube] client_secret.json not found!")
                print("Get it from: https://console.cloud.google.com/apis/credentials")
                print("Enable YouTube Data API v3, create OAuth 2.0 credentials")
                print("Download JSON and save as client_secret.json in project root")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        os.makedirs(TOKEN_DIR, exist_ok=True)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return creds


def upload_video(video_path, script, config):
    creds = authenticate()
    if not creds:
        print("[YouTube] Auth failed. Skipping upload.")
        return None

    title = script["title"]
    tags = script.get("tags", [])
    description = (
        f"{title}\n\n"
        f"Подпишись на канал, чтобы не пропустить новые видео!\n\n"
        f"#{' #'.join(tags)}"
    )

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        youtube = build("youtube", "v3", credentials=creds)
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = request.execute()
        video_id = response.get("id")
        video_url = f"https://youtu.be/{video_id}"
        print(f"[YouTube] Uploaded: {video_url}")
        return video_url

    except Exception as e:
        print(f"[YouTube upload error] {e}")
        return None


if __name__ == "__main__":
    from config import config
    from generate_script import fetch_or_generate_script

    script = fetch_or_generate_script(config)
    video_path = os.path.join(
        os.path.dirname(__file__), "output", "final_video.mp4"
    )
    if os.path.exists(video_path):
        upload_video(video_path, script, config)
    else:
        print("No video found. Run main.py first.")
