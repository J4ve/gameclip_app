"""
Arrangement Screen - Video preview & ordering (Step 2)
"""

import flet as ft
from configs.config import Config


class ArrangementScreen:
    """Second screen: Arrange clips and preview"""
    
    def __init__(self, videos=None, on_next=None, on_back=None):
        self.videos = videos or []  # List of selected videos from Step 1
        self.on_next = on_next  # Callback for "Next" button
        self.on_back = on_back  # Callback for "Back" button
        self.file_list = ft.Column(spacing=5)
        # TODO: Initialize preview state
        # TODO: Initialize playback controls
        
    def build(self):
        """Build and return arrangement screen layout (Frame 2)"""
        # TODO: Left panel - Video list with reorder controls
        # TODO: Center - Video preview area
        # TODO: Bottom - Progress bar with playback controls (play, pause, skip)
        # TODO: Top right - "Arrange By" dropdown (Name, Date, Size, Custom)
        # TODO: Add remove buttons for each video
        # TODO: Add "Back" and "Next" navigation buttons
        self.file_list_container = ft.Container(
            content=ft.Column(
                [self.file_list],
                scroll=ft.ScrollMode.AUTO,
            ),
            width=500,
            height=60,  # Initial minimum height
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            padding=10,
        )

        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Arrange Videos", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            # Left: Video list
                            ft.Column([ft.Text("Video list goes here")], expand=1),
                            # Center: Preview
                            ft.Container(
                                content=ft.Text("Video Preview"),
                                bgcolor=ft.Colors.BLACK12,
                                expand=2,
                                alignment=ft.alignment.center,
                            ),
                        ],
                        expand=True,
                    ),
                    # Placeholder for playback controls
                    # Placeholder for Back/Next buttons
                ],
                spacing=20,
            ),
            padding=20,
            expand=True,
        )
