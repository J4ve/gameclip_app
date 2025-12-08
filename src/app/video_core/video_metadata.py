"""
Video Metadata Extractor - Get video properties using ffprobe
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


# Global cache to avoid re-extracting metadata for the same files
_metadata_cache: Dict[str, 'VideoMetadata'] = {}


class VideoMetadata:
    """Video metadata information"""
    
    def __init__(self, file_path: str, use_cache: bool = True):
        self.file_path = file_path
        self.codec: Optional[str] = None
        self.resolution: Optional[str] = None
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self.framerate: Optional[float] = None
        self.duration: Optional[float] = None
        self.bitrate: Optional[int] = None
        self.file_size: Optional[int] = None
        self.error: Optional[str] = None
        
        # Check cache first
        if use_cache and file_path in _metadata_cache:
            cached = _metadata_cache[file_path]
            self.codec = cached.codec
            self.resolution = cached.resolution
            self.width = cached.width
            self.height = cached.height
            self.framerate = cached.framerate
            self.duration = cached.duration
            self.bitrate = cached.bitrate
            self.file_size = cached.file_size
            self.error = cached.error
        else:
            self._extract_metadata()
            if use_cache:
                _metadata_cache[file_path] = self
    
    def _extract_metadata(self):
        """Extract video metadata using ffprobe"""
        try:
            # Get video stream info
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name,width,height,r_frame_rate,bit_rate",
                "-show_entries", "format=duration,size",
                "-of", "json",
                self.file_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Extract stream data
                if "streams" in data and len(data["streams"]) > 0:
                    stream = data["streams"][0]
                    self.codec = stream.get("codec_name", "unknown").upper()
                    self.width = stream.get("width")
                    self.height = stream.get("height")
                    
                    if self.width and self.height:
                        self.resolution = f"{self.width}x{self.height}"
                    
                    # Parse framerate (format: "30/1" or "30000/1001")
                    fps_str = stream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        num, den = map(float, fps_str.split("/"))
                        if den > 0:
                            self.framerate = round(num / den, 2)
                    
                    # Bitrate
                    bitrate_str = stream.get("bit_rate")
                    if bitrate_str:
                        self.bitrate = int(bitrate_str)
                
                # Extract format data
                if "format" in data:
                    fmt = data["format"]
                    duration_str = fmt.get("duration")
                    if duration_str:
                        self.duration = float(duration_str)
                    
                    size_str = fmt.get("size")
                    if size_str:
                        self.file_size = int(size_str)
            else:
                self.error = f"ffprobe failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            self.error = "Metadata extraction timed out"
        except FileNotFoundError:
            self.error = "ffprobe not found"
        except Exception as e:
            self.error = f"Error extracting metadata: {str(e)}"
    
    def is_valid(self) -> bool:
        """Check if metadata was extracted successfully"""
        return self.error is None and self.codec is not None
    
    def get_display_text(self, include_filename: bool = True) -> str:
        """Get formatted display text for UI"""
        if not self.is_valid():
            return f"Error: {self.error}" if self.error else "Unknown"
        
        parts = []
        
        if include_filename:
            parts.append(Path(self.file_path).name)
        
        if self.codec:
            parts.append(f"Codec: {self.codec}")
        
        if self.resolution:
            parts.append(f"Res: {self.resolution}")
        
        if self.framerate:
            parts.append(f"FPS: {self.framerate}")
        
        if self.duration:
            mins = int(self.duration // 60)
            secs = int(self.duration % 60)
            parts.append(f"Duration: {mins}m {secs}s")
        
        return " | ".join(parts)
    
    def get_short_info(self) -> str:
        """Get short metadata info (codec, resolution, fps)"""
        if not self.is_valid():
            return "⚠️ Unknown"
        
        parts = []
        if self.codec:
            parts.append(self.codec)
        if self.resolution:
            parts.append(self.resolution)
        if self.framerate:
            parts.append(f"{self.framerate}fps")
        
        return " • ".join(parts) if parts else "No info"
    
    def matches(self, other: 'VideoMetadata') -> bool:
        """Check if this video has compatible properties with another"""
        if not self.is_valid() or not other.is_valid():
            return False
        
        return (
            self.codec == other.codec and
            self.resolution == other.resolution and
            self.framerate == other.framerate
        )
    
    def get_compatibility_issues(self, other: 'VideoMetadata') -> list[str]:
        """Get list of compatibility issues with another video"""
        issues = []
        
        if not self.is_valid():
            issues.append("Invalid metadata for first video")
            return issues
        
        if not other.is_valid():
            issues.append("Invalid metadata for second video")
            return issues
        
        if self.codec != other.codec:
            issues.append(f"Different codecs: {self.codec} vs {other.codec}")
        
        if self.resolution != other.resolution:
            issues.append(f"Different resolutions: {self.resolution} vs {other.resolution}")
        
        if self.framerate != other.framerate:
            issues.append(f"Different framerates: {self.framerate}fps vs {other.framerate}fps")
        
        return issues


def get_file_size_str(size_bytes: int) -> str:
    """Convert file size to human-readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def clear_metadata_cache():
    """Clear the metadata cache (useful when files change or to free memory)"""
    global _metadata_cache
    _metadata_cache.clear()


def check_videos_compatibility(video_paths: list[str]) -> tuple[bool, list[str]]:
    """
    Check if all videos are compatible for merging
    
    Returns:
        (is_compatible, list_of_issues)
    """
    if not video_paths:
        return False, ["No videos provided"]
    
    if len(video_paths) == 1:
        return True, []
    
    # Extract metadata for all videos
    metadata_list = [VideoMetadata(path) for path in video_paths]
    
    # Check if any failed
    failed = [m for m in metadata_list if not m.is_valid()]
    if failed:
        return False, [f"Failed to read metadata from {len(failed)} video(s)"]
    
    # Compare all videos with the first one
    first_video = metadata_list[0]
    all_issues = []
    
    for i, video in enumerate(metadata_list[1:], start=2):
        issues = first_video.get_compatibility_issues(video)
        if issues:
            for issue in issues:
                all_issues.append(f"Video {i}: {issue}")
    
    return len(all_issues) == 0, all_issues
