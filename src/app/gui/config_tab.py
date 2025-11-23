"""
Config Tab - Application settings
"""

import flet as ft


class ConfigTab:
    """Config tab layout and components"""
    
    def __init__(self):
        pass
        # TODO: Initialize state variables
        
    def build(self):
        """Build and return config tab layout"""
        # TODO: Add profile selection/creation
        # TODO: Add metadata templates (title, description, tags)
        # TODO: Add YouTube API settings
        # TODO: Add FFmpeg settings
        # TODO: Add save/load buttons
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Config Tab - Build your UI here", size=20),
                    # Placeholder for settings forms
                    # Placeholder for profile management
                    # Placeholder for API configuration
                ],
                spacing=10,
            ),
            padding=20,
        )
