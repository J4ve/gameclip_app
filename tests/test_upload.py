import sys
import os
from pathlib import Path
# Add src/ to sys.path so we can import uploader and other project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
from uploader.auth import get_youtube_service

yt = get_youtube_service()
service = yt.service

video_filename = "test.mp4"  # Change to your actual filename
video_path = str(Path.home() / "Downloads" / video_filename)


request = service.videos().insert(
    part="snippet,status",
    body={
        "snippet": {
            "title": "Test Uploado",
            "description": "Uploaded via API",
            "tags": ["test", "api"],
            "categoryId": "22"
        },
            "status": {
                "privacyStatus": "unlisted",
                "selfDeclaredMadeForKids": False
        }
    },
    media_body=video_path
)
response = request.execute()
print("Upload response:", response)