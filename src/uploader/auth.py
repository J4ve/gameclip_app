"""
YouTube Auth Module
Handles OAuth 2.0 authentication for Google APIs.
"""

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.path_helper import get_resource_path


TOKEN_PATH = "token.pickle"
CLIENT_SECRET = get_resource_path(os.path.join("configs", "client_secret.json"))
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/userinfo.profile", 
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"  # Google automatically adds this, so include it explicitly
]


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
        try:
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
                
            # Check if scopes match - if not, delete token and start fresh
            if creds and hasattr(creds, 'scopes'):
                current_scopes = set(SCOPES)
                stored_scopes = set(creds.scopes) if creds.scopes else set()
                if current_scopes != stored_scopes:
                    print(f"Scope mismatch detected. Clearing stored credentials...")
                    print(f"Current: {sorted(current_scopes)}")
                    print(f"Stored: {sorted(stored_scopes)}")
                    os.remove(TOKEN_PATH)
                    creds = None
                    
        except Exception as e:
            print(f"Error loading token file: {e}")
            # Delete corrupted token file
            try:
                os.remove(TOKEN_PATH)
            except:
                pass
            creds = None

    # If no valid credentials, start OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                # Delete expired token and start fresh
                if os.path.exists(TOKEN_PATH):
                    try:
                        os.remove(TOKEN_PATH)
                    except:
                        pass
                creds = None
        
        if not creds:
            # Clear any Google OAuth cache that might be interfering
            cache_paths = [
                os.path.expanduser("~/.google_auth_cache"),
                os.path.expanduser("~/.config/gcloud"),
                "token.pickle"
            ]
            
            for cache_path in cache_paths:
                if os.path.exists(cache_path):
                    try:
                        if os.path.isfile(cache_path):
                            os.remove(cache_path)
                        print(f"Cleared cache: {cache_path}")
                    except:
                        pass
            
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
            
            print("Starting fresh Google authentication...")
            
            # Try multiple ports to avoid conflicts
            ports_to_try = [8080, 8081, 8082, 9090, 0]  # 0 = random available port
            auth_success = False
            
            for port in ports_to_try:
                try:
                    print(f"Attempting authentication on port {port}...")
                    creds = flow.run_local_server(
                        port=port,
                        open_browser=True,
                        success_message="Authentication successful! You can close this window.",
                        timeout_seconds=120  # 2 minute timeout
                    )
                    print(f"OAuth authentication completed successfully! Got credentials: {creds is not None}")
                    auth_success = True
                    break
                except Exception as ex:
                    print(f"Port {port} failed: {ex}")
                    
                    # For scope errors, try to clear the token and continue
                    if "Scope has changed" in str(ex):
                        print("Scope change detected. Clearing cached tokens...")
                        # Delete the problematic token file
                        if os.path.exists(TOKEN_PATH):
                            try:
                                os.remove(TOKEN_PATH)
                                print(f"Removed token file: {TOKEN_PATH}")
                            except Exception:
                                pass
                        # Continue to next port instead of breaking
                        continue
                    
                    # For other errors, continue to next port
                    if port != ports_to_try[-1]:  # Not the last port
                        continue
            
            # If all ports failed, try one final attempt with fresh setup
            if not auth_success:
                print("All standard ports failed. Trying final fresh authentication...")
                try:
                    # Clear any remaining cached data
                    for cache_file in [TOKEN_PATH, "token.json", ".credentials"]:
                        if os.path.exists(cache_file):
                            try:
                                os.remove(cache_file)
                                print(f"Cleared cache file: {cache_file}")
                            except:
                                pass
                    
                    # Create completely fresh flow
                    fresh_flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
                    creds = fresh_flow.run_local_server(
                        port=0,  # Use random available port
                        open_browser=True,
                        success_message="Authentication successful! You can close this window.",
                        timeout_seconds=90
                    )
                    print(f"Fresh authentication succeeded! Got credentials: {creds is not None}")
                    auth_success = True
                    
                except Exception as final_ex:
                    print(f"Final authentication attempt failed: {final_ex}")
                    auth_success = False
            
            # Check if we actually got valid credentials
            if not auth_success or not creds:
                raise Exception("Authentication completed but failed to obtain valid credentials. Please try again.")
            
            # Save the credentials for next time
            if creds and creds.valid:
                try:
                    with open(TOKEN_PATH, "wb") as token:
                        pickle.dump(creds, token)
                    print(f"Credentials saved to {TOKEN_PATH}")
                except Exception as e:
                    print(f"Warning: Could not save credentials: {e}")
            else:
                print(f"Warning: Invalid credentials received. Valid: {creds.valid if creds else 'creds is None'}")
                if not creds:
                    raise Exception("Failed to obtain valid credentials from OAuth flow")
                elif not creds.valid:
                    raise Exception("Obtained credentials are not valid")

    # Final validation before building service
    if not creds:
        raise Exception("No credentials available after authentication")
    
    if not creds.valid:
        print(f"Credentials not valid. Expired: {creds.expired if hasattr(creds, 'expired') else 'unknown'}")
        # Try to refresh if possible
        if hasattr(creds, 'refresh_token') and creds.refresh_token:
            try:
                print("Attempting to refresh expired credentials...")
                creds.refresh(Request())
                print("Credentials refreshed successfully!")
            except Exception as refresh_ex:
                print(f"Failed to refresh credentials: {refresh_ex}")
                raise Exception("Credentials are not valid and cannot be refreshed")
        else:
            raise Exception("Credentials are not valid and cannot be refreshed")

    # Build and return the YouTube service
    print("Building YouTube service...")
    service = build("youtube", "v3", credentials=creds)
    print("YouTube service built successfully!")
    return YouTubeService(service, creds)