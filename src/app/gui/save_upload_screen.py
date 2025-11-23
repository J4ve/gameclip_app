"""
Save/Upload Screen - Final configuration & upload (Step 3)
"""

import flet as ft
from configs.config import Config


class SaveUploadScreen:
    """Third screen: Configure output and upload settings"""
    
    def __init__(self, videos=None, on_save=None, on_upload=None, on_back=None):
        self.videos = videos or []  # List of arranged videos from Step 2
        self.on_save = on_save  # Callback for "Save" button
        self.on_upload = on_upload  # Callback for "Save / Upload" button
        self.on_back = on_back  # Callback for "Back" button
        # TODO: Initialize form fields
        # TODO: Load default values from Config
        
    def build(self):
        """Build and return save/upload screen layout (Frame 4)"""
        # TODO: Left panel - Final video list
        # TODO: Center - Video preview
        # TODO: Right panel - Configuration sidebar
        #   - Save Settings section (filename, format, resolution)
        #   - Upload Settings section (title, tags, visibility, description)
        #   - Status Tags section
        # TODO: Add "Save" and "Save / Upload" buttons
        # TODO: Add "Back" button
        # TODO: Add progress indicator for upload
        
        return ft.Container(
            content=ft.Row(
                [
                    # Left: Video list
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Selected Videos", size=16, weight=ft.FontWeight.BOLD),
                                # Placeholder for video list
                            ],
                        ),
                        expand=1,
                        padding=10,
                    ),
                    
                    # Center: Preview
                    ft.Container(
                        content=ft.Container(
                            content=ft.Text("Video Preview"),
                            bgcolor=ft.colors.BLACK12,
                            alignment=ft.alignment.center,
                        ),
                        expand=2,
                        padding=10,
                    ),
                    
                    # Right: Settings
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Save / Upload", size=20, weight=ft.FontWeight.BOLD),
                                ft.Divider(),
                                
                                # Save Settings
                                ft.Text("Save Settings", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Filename: {Config.DEFAULT_OUTPUT_FORMAT}"),
                                ft.Text(f"Format: {Config.DEFAULT_CODEC}"),
                                # TODO: Add TextFields, Dropdowns
                                
                                ft.Divider(),
                                
                                # Upload Settings
                                ft.Text("Upload Settings", size=14, weight=ft.FontWeight.BOLD),
                                # TODO: Add Title, Tags, Visibility, Description fields
                                
                                ft.Divider(),
                                
                                # Buttons
                                ft.ElevatedButton("Save", icon=ft.icons.SAVE),
                                ft.ElevatedButton("Save / Upload", icon=ft.icons.UPLOAD),
                                
                                # Placeholder for status tags
                            ],
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=1,
                        padding=10,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                    ),
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )
