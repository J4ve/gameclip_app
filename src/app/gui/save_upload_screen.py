"""
Save/Upload Screen - Final configuration & upload (Step 3)
"""

import flet as ft
from configs.config import Config
# TODO: import date library thingy para sa placeholder filename

class SaveUploadScreen:
    """Third screen: Configure output and upload settings"""
    
    def __init__(self, videos=None, page=None, on_save=None, on_upload=None, on_back=None):
        self.page = page
        self.videos = videos or []  # List of arranged videos from Step 2
        self.on_save = on_save  # Callback for "Save" button
        self.on_upload = on_upload  # Callback for "Save / Upload" button
        self.on_back = on_back  # Callback for "Back" button
        self.main_window = None # para mareference ni main_window sarili in this class
        self.file_list = ft.Column(spacing=5)
        
        # TODO: Initialize form fields
        # TODO: Load default values from Config

    def set_videos(self, videos):
        self.videos = videos or []
        self.selected_video_index = 0
        
    def build(self):
        """Build and return save/upload screen layout (Frame 4)"""

        # Save Settings section
        filename_field = ft.TextField(label="Filename", value=f"{Config.DEFAULT_OUTPUT_FORMAT}")
        format_dropdown = ft.Dropdown(
            label="File Type",
            options=[ft.dropdown.Option(fmt) for fmt in Config.SUPPORTED_VIDEO_FORMATS],
            value=Config.DEFAULT_VIDEO_FORMAT,
            width=150,
            menu_height=200,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREY_900,
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
        )
        codec_dropdown = ft.Dropdown(
            label="Codec",
            options=[ft.dropdown.Option(codec) for codec in Config.SUPPORTED_CODECS],
            value=Config.DEFAULT_CODEC,
            width=150,
            menu_height=200,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREY_900,
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
        )
        save_settings_section = ft.Column([
            ft.Text("Save Settings", size=14, weight=ft.FontWeight.BOLD),
            filename_field,
            format_dropdown,
            codec_dropdown,
            ft.Divider(),
        ])

        # Upload Settings section
        title_field = ft.TextField(label="Title")
        tags_field = ft.TextField(label="Tags (comma separated)")
        visibility_dropdown = ft.Dropdown(
            label="Visibility",
            options=[
                ft.dropdown.Option("Public"),
                ft.dropdown.Option("Unlisted"),
                ft.dropdown.Option("Private"),
            ],
            value="Public",
            width=150,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREY_900,
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
        )
        description_field = ft.TextField(label="Description", multiline=True, min_lines=3, max_lines=5)
        upload_settings_section = ft.Column([
            ft.ElevatedButton("Edit Upload Settings", on_click=lambda e: open_upload_settings_dialog(e)),
            ft.Divider(),
        ])

        # Buttons section
        buttons_section = ft.Column([
            ft.ElevatedButton("Save", icon=ft.Icons.SAVE),
            ft.ElevatedButton("Upload", icon=ft.Icons.UPLOAD),
            # Placeholder for status tags
        ])

        # Dialog logic
        def close_upload_settings_dialog(e):
            upload_settings_dialog.open = False
            self.page.update()

        def open_upload_settings_dialog(e):
            upload_settings_dialog.open = True
            self.page.update()

        upload_settings_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Settings"),
            content=ft.Column([
                title_field,
                tags_field,
                visibility_dropdown,
                description_field,
            ], spacing=10),
            actions=[
                ft.TextButton("Save", on_click=close_upload_settings_dialog),
                ft.TextButton("Cancel", on_click=close_upload_settings_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            content_padding=ft.padding.only(left=200, right=200),
            on_dismiss=lambda e: print("Upload settings dialog dismissed!"),
        )

        # Add dialog to page overlay
        if self.page:
            self.page.overlay.append(upload_settings_dialog)

        # Build video list (no arrange/remove buttons)
        video_list_controls = []
        if not self.videos:
            video_list_controls.append(
                ft.Text("No videos selected.", color=ft.Colors.WHITE70)
            )
        else:
            for i, video_path in enumerate(self.videos):
                video_name = video_path.split('/')[-1] if '/' in video_path else video_path.split('\\')[-1]
                video_item = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(str(i + 1), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            width=30, height=30, bgcolor=ft.Colors.with_opacity(0.8, "#00ACC1"),
                            border_radius=15, alignment=ft.alignment.center,
                        ),
                        ft.Text(video_name, color=ft.Colors.WHITE, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, "#FFFFFF") if i == 0 else ft.Colors.with_opacity(0.02, "#FFFFFF"),
                    border_radius=8,
                )
                video_list_controls.append(video_item)

        # Calculate dynamic height for video list container
        num_videos = len(self.videos)
        video_list_height = min(max(num_videos * 40, 80), 160)  # 40px per video, min 80, max 160 (fits 4 videos)

        # Main layout
        return ft.Container(
            content=ft.Row(
                [
                    # Left column: Video list above, preview below
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Selected Videos", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    content=ft.Column(video_list_controls, scroll=ft.ScrollMode.AUTO),
                                    height=video_list_height,
                                    bgcolor=ft.Colors.with_opacity(0.03, "#FFFFFF"),
                                    border_radius=8,
                                    padding=8,
                                ),
                                ft.Container(height=10), # Spacer
                                ft.Text("Video Preview", size=16, weight=ft.FontWeight.BOLD),
                                ft.Container(
                                    content=ft.Text("Video Preview"),
                                    bgcolor=ft.Colors.BLACK12,
                                    alignment=ft.alignment.center,
                                    height=200,
                                    border_radius=8,
                                ),
                            ],
                            expand=True,
                            spacing=10,
                        ),
                        expand=1,
                        padding=10,
                    ),

                    # Right column: Settings (larger)
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text("Save / Upload", size=20, weight=ft.FontWeight.BOLD),
                                ft.Divider(),
                                save_settings_section,
                                upload_settings_section,
                                buttons_section,
                            ],
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        expand=2,
                        padding=20,
                        bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
                    ),
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )