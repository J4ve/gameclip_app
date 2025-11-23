"""Configuration management for the app"""
import os
from dotenv import load_dotenv

class Config:
    """Application configuration"""

    APP_TITLE = "Video Merger"
    APP_WIDTH = 1200
    APP_HEIGHT = 900

    SUPPORTED_VIDEO_FORMATS = [".mp4", ".mkv", ".mov", ".avi"]

    