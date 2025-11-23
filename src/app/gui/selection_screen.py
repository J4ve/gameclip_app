"""
Selection Screen - Video selection (Step 1)
"""

import flet as ft
from configs.config import Config


class SelectionScreen:
    """First screen: File selection with drag & drop"""
    
    def __init__(self, on_next=None):
        self.on_next = on_next  # Callback for "Next" button
        self.selected_files = []  # Store selected video files
        # TODO: Initialize FilePicker
        # TODO: Initialize drag & drop state
        
    def build(self):
        """Build and return upload screen layout (Frame 1)"""
        # TODO: Add drag & drop zone
        # TODO: Add "Select File" button with FilePicker
        # TODO: Display selected files count/list
        # TODO: Add "Next" button (calls self.on_next)
        # TODO: Validate file formats (Config.SUPPORTED_VIDEO_FORMATS)
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Select Videos", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Drag and drop video files here", size=16),
                    ft.Text(f"Supported formats: {', '.join(Config.SUPPORTED_VIDEO_FORMATS)}", size=12),
                    # Placeholder for drag & drop zone
                    # Placeholder for file browser button
                    # Placeholder for "Next" button
                ],
                spacing=20,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
            expand=True,
        )