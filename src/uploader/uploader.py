"""
YouTube Uploader Module
Handles all non-GUI video upload logic
"""

from .auth import get_youtube_service
from typing import Optional, Callable, Dict, Any
from pathlib import Path


class UploadSettings:
    """Container for all upload settings"""
    def __init__(
        self,
        title: str,
        description: str,
        tags: list,
        visibility: str = "unlisted",
        category_id: str = "22",
        made_for_kids: bool = False,
        embeddable: bool = True,
        publish_at: Optional[str] = None,
        record_stats: bool = True
    ):
        self.title = title
        self.description = description
        self.tags = tags if isinstance(tags, list) else [t.strip() for t in tags.split(",") if t.strip()]
        self.visibility = visibility.lower()
        self.category_id = category_id
        self.made_for_kids = made_for_kids
        self.embeddable = embeddable
        self.publish_at = publish_at
        self.record_stats = record_stats


class YouTubeUploader:
    """Handles YouTube video uploads without GUI"""
    
    def __init__(self):
        self.youtube_service = None
        self.current_upload_id = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth.
        Returns: bool - True if successful
        """
        try:
            self.youtube_service = get_youtube_service()
            return True
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def upload_video(
        self,
        video_path: str,
        settings: UploadSettings,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Upload a single video to YouTube.
        
        Args:
            video_path: Path to video file
            settings: UploadSettings object with metadata
            progress_callback: Function to call with (percentage, message)
        
        Returns: Response dict with video_id and other YouTube data
        """
        if not self.youtube_service:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        if progress_callback:
            progress_callback(0, "Preparing upload...")
        
        # Check file exists
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        try:
            if progress_callback:
                progress_callback(10, "Building upload request...")
            
            # Build request body
            body = self._build_request_body(settings)
            
            if progress_callback:
                progress_callback(20, "Uploading video file...")
            
            # Create upload request
            request = self.youtube_service.service.videos().insert(
                part="snippet,status",
                body=body,
                media_body=video_path
            )
            
            # Execute upload
            response = request.execute()
            
            if progress_callback:
                progress_callback(100, "Upload complete!")
            
            self.current_upload_id = response.get('id')
            return {
                'success': True,
                'video_id': response.get('id'),
                'title': response.get('snippet', {}).get('title'),
                'status': response.get('status', {}).get('uploadStatus'),
                'response': response
            }
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, f"Upload failed: {str(e)}")
            raise
    
    def _build_request_body(self, settings: UploadSettings) -> Dict[str, Any]:
        """
        Build the request body for YouTube API.
        """
        body = {
            "snippet": {
                "title": settings.title,
                "description": settings.description,
                "tags": settings.tags,
                "categoryId": settings.category_id
            },
            "status": {
                "privacyStatus": settings.visibility,
                "selfDeclaredMadeForKids": settings.made_for_kids,
                "embeddable": settings.embeddable,
                "publicStatsViewable": settings.record_stats
            }
        }
        
        # Add scheduled publish time if provided
        if settings.publish_at:
            body["status"]["publishAt"] = settings.publish_at
        
        return body
    
    def get_upload_status(self, video_id: str) -> Dict[str, Any]:
        """
        Get the status of an uploaded video.
        """
        if not self.youtube_service:
            raise Exception("Not authenticated.")
        
        try:
            request = self.youtube_service.service.videos().list(
                part="status,processingDetails",
                id=video_id
            )
            response = request.execute()
            
            if response.get('items'):
                video = response['items'][0]
                return {
                    'status': video.get('status', {}).get('uploadStatus'),
                    'processing': video.get('processingDetails', {}).get('processingProgress'),
                    'failure_reason': video.get('processingDetails', {}).get('processingFailureReason')
                }
            return None
        except Exception as e:
            raise Exception(f"Failed to get upload status: {str(e)}")

    def process_queue(self):
        """
        Process the upload queue with progress tracking.
        """
        # TODO: Upload each video, update progress bars
        pass

    def apply_metadata_template(self, video_path):
        """
        Apply metadata template to a video.
        """
        # TODO: Use template system for title/description/tags
        pass

    def save_progress(self):
        """
        Save upload progress to disk (optional).
        """
        # TODO: Write progress to file
        pass