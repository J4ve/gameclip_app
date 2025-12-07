"""Configuration management for the app"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    APP_TITLE = "Video Merger"
    APP_WIDTH = 1200
    APP_HEIGHT = 700

    DEFAULT_OUTPUT_FORMAT = "merged_video" #placeholder muna, sa program na madagdag ng ".mp4" saka date

    SUPPORTED_VIDEO_FORMATS = [
        ".mp4",   # MPEG-4 Part 14
        ".mkv",   # Matroska
        ".mov",   # QuickTime
        ".avi",   # Audio Video Interleave
        ".flv",   # Flash Video
        ".wmv",   # Windows Media Video
        ".webm",  # WebM
        ".mpg",   # MPEG-1/2
        ".mpeg",  # MPEG-1/2
        ".m4v",   # MPEG-4 Video
        ".3gp",   # 3GPP
        ".ts",    # MPEG Transport Stream
        ".ogv",   # Ogg Video
        ".vob",   # DVD Video Object
        ".f4v",   # Flash MP4 Video
        ".mts",   # AVCHD Video
        ".m2ts",  # Blu-ray/AVCHD Video
        ".divx",  # DivX
        ".xvid",  # Xvid
        ".rm",    # RealMedia
        ".rmvb",  # RealMedia Variable Bitrate
        ".asf",   # Advanced Systems Format
        ".mxf",   # Material Exchange Format
        ".yuv",   # Raw YUV Video
        ".dv",    # Digital Video
        ".amv",   # Anime Music Video
        ".nsv",   # Nullsoft Streaming Video
    ]
    DEFAULT_VIDEO_FORMAT = SUPPORTED_VIDEO_FORMATS[0]

    SUPPORTED_CODECS = [
        "H.264",      # libx264
        "H.265",      # libx265
        "VP8",        # libvpx
        "VP9",        # libvpx-vp9
        "MPEG-4",     # mpeg4
        "MPEG-2",     # mpeg2video
        "ProRes",     # prores
        "Theora",     # libtheora
        "AV1",        # libaom-av1
        "WMV",        # wmv2
    ]
    DEFAULT_CODEC = SUPPORTED_CODECS[0]

