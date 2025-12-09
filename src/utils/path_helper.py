"""
Path Helper Module
Provides cross-platform path resolution for both development and PyInstaller packaged environments.
"""

import os
import sys


def get_base_path():
    """
    Get the base path for the application.
    
    When running in development:
        Returns the project root directory (parent of src/)
    
    When running as PyInstaller bundle:
        Returns sys._MEIPASS (the temporary folder where PyInstaller extracts files)
    
    Returns:
        str: Base path for the application
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        return sys._MEIPASS
    else:
        # Running in development
        # Go up from src/utils/ to project root
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_resource_path(relative_path):
    """
    Get absolute path to a resource file.
    
    Args:
        relative_path (str): Relative path from project root (e.g., 'configs/client_secret.json')
    
    Returns:
        str: Absolute path to the resource
    """
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)
