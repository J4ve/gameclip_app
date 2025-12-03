"""
YouTube Auth Module
Handles OAuth 2.0 authentication for Google APIs.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import os


TOKEN_PATH = "token.pickle"
CLIENT_SECRET = os.path.join(os.path.dirname(__file__), "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeService:
    """
    Wrapper for YouTube API service and credentials.
    """
    def __init__(self, service, credentials):
        self.service = service
        self.credentials = credentials

def get_youtube_service():
    """
    Authenticate and return a YouTubeService object.
    Loads token.pickle if available, saves new tokens when refreshed.
    No UI code — backend only.
    Returns:
        YouTubeService: Object with .service and .credentials
    """
    # Load existing token if available
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            try:
                creds = flow.run_local_server(port=8080)
            except Exception:
                print("Local server failed, falling back to manual console authentication.")
                creds = flow.run_console()
            # Save the credentials for next time
            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)

    # Build and return the YouTube service
    service = build("youtube", "v3", credentials=creds)
    return YouTubeService(service, creds)