"""Configuration management for the app"""
import os
from dotenv import load_dotenv

class Config:
    """Application configuration"""

    APP_TITLE = "Video Merger"
    APP_WIDTH = 1200
    APP_HEIGHT = 900

    SUPPORTED_VIDEO_FORMATS = [".mp4", ".mkv", ".mov", ".avi"]
    DEFAULT_OUTPUT_FORMAT = [".mp4"] #placeholder muna
    DEFAULT_CODEC = [] #placeholder aa

    