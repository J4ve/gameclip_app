"""
Selection Screen - Video selection (Step 1)
"""

import flet as ft
from configs.config import Config
from pathlib import Path


class SelectionScreen:
    """First screen: File selection with FilePicker"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_files = []  # Store selected video files
        self.file_list = ft.Column(spacing=5)  # Display selected files
        self.select_zone_container = None  # Will store the selection zone reference
        self.files_display = None  # Will store the files display reference
        self.file_list_container = None  # Will store the scrollable container

        # Initialize FilePicker
        self.file_picker = ft.FilePicker(on_result=self.handle_file_selection)
        self.page.overlay.append(self.file_picker)
        
    def handle_file_selection(self, e: ft.FilePickerResultEvent):
        """Handle files selected from FilePicker"""
        if e.files:
            for file in e.files:
                file_path = file.path
                file_ext = Path(file_path).suffix.lower()
                
                # Validate file format
                if file_ext in Config.SUPPORTED_VIDEO_FORMATS:
                    if file_path not in self.selected_files:
                        self.selected_files.append(file_path)
                        # Add to visual list
                        self.file_list.controls.append(
                            ft.Row([
                                ft.Icon(ft.Icons.VIDEO_FILE, size=16),
                                ft.Text(file.name, size=12, expand=True),
                                ft.IconButton(
                                    icon=ft.Icons.CLOSE,
                                    icon_size=16,
                                    on_click=lambda _, path=file_path: self.remove_file(path)
                                ),
                            ])
                        )
                else:
                    # Show error for invalid format
                    unssuported_file_snackbar = ft.SnackBar(
                        content=ft.Text(f"Unsupported format: {file_ext}"),
                        bgcolor=ft.Colors.ERROR,
                    )
                    self.page.overlay.append(unssuported_file_snackbar)
                    unssuported_file_snackbar.open = True
            
            # Toggle visibility based on files
            if self.files_display and self.select_zone_container:
                has_files = len(self.selected_files) > 0
                self.files_display.visible = has_files
                self.select_zone_container.visible = not has_files
            
            # Adjust container height based on number of files (each row ~30px)
            if self.file_list_container:
                num_files = len(self.selected_files)
                # Min 60px, max 200px, ~30px per file
                new_height = min(max(num_files * 30, 90), 200)
                self.file_list_container.height = new_height
            
            self.page.update()
    
    def remove_file(self, file_path):
        """Remove file from selection"""
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            # Rebuild file list display
            self.file_list.controls = [
                ft.Row([
                    ft.Icon(ft.Icons.VIDEO_FILE, size=16),
                    ft.Text(Path(f).name, size=12, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=16,
                        on_click=lambda _, path=f: self.remove_file(path)
                    ),
                ])
                for f in self.selected_files
            ]
            
            # Toggle visibility when no files left
            if self.files_display and self.select_zone_container:
                has_files = len(self.selected_files) > 0
                self.files_display.visible = has_files
                self.select_zone_container.visible = not has_files
            
            # Adjust container height based on number of files
            if self.file_list_container:
                num_files = len(self.selected_files)
                new_height = min(max(num_files * 30, 60), 200)
                self.file_list_container.height = new_height
            
            self.page.update()
    
    def build(self):
        """Build and return selection screen layout (Frame 1)"""

        # Monokai-like dark theme
        monokai_bg = ft.Colors.with_opacity(0.95, "#272822")
        dark_border = ft.Colors.GREY_700
        dark_text = ft.Colors.GREY_100
        accent = ft.Colors.BLUE_400

        # Clickable selection zone with improved hover effect
        self.select_zone_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.FILE_UPLOAD, size=64, color=accent),
                    ft.Text("Click to Select Videos", size=18, weight=ft.FontWeight.BOLD, color=dark_text),
                    ft.Text("Browse for video files to merge", size=12, color=ft.Colors.GREY_400),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            width=400,
            height=200,
            border=ft.border.all(2, dark_border),
            border_radius=12,
            bgcolor=monokai_bg,
            alignment=ft.alignment.center,
            on_click=lambda _: self.file_picker.pick_files(
                allow_multiple=True,
                file_type=ft.FilePickerFileType.VIDEO,
            ),
            visible=True,  # Will be set below
        )

        # Selected files list (only shows when files are selected)
        num_files = len(self.selected_files)
        # Show up to 15 videos (each ~40px), min 200px, max 600px
        file_list_height = min(max(num_files * 40, 200), 600)
        self.file_list_container = ft.Container(
            content=ft.Column(
                [self.file_list],
                scroll=ft.ScrollMode.AUTO,
            ),
            width=700,
            height=file_list_height,
            border=ft.border.all(1, dark_border),
            border_radius=10,
            padding=15,
            bgcolor=monokai_bg,
        )

        self.files_display = ft.Container(
            content=ft.Column([
                ft.Text("Selected Files:", size=14, weight=ft.FontWeight.BOLD, color=accent),
                self.file_list_container,
                ft.TextButton(
                    text="Add More Videos",
                    icon=ft.Icons.ADD,
                    on_click=lambda _: self.file_picker.pick_files(
                        allow_multiple=True,
                        file_type=ft.FilePickerFileType.VIDEO,
                    ),
                    style=ft.ButtonStyle(color=dark_text, bgcolor=accent),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            ),
            visible=False,  # Will be set below
            padding=10,
            bgcolor=monokai_bg,
            border_radius=10,
        )

        # Set visibility based on whether files are selected
        has_files = num_files > 0
        self.files_display.visible = has_files
        self.select_zone_container.visible = not has_files

        return ft.Container(
            content=ft.Column(
                [
                    # Header
                    ft.Text("Select Videos", size=24, weight=ft.FontWeight.BOLD, color=accent),
                    ft.Text(f"Supported formats: .mp4, .mkv, .mov, .avi, and more…", size=12, color=dark_text),

                    ft.Container(height=20),  # Spacer

                    # Selection zone (hidden when files are selected)
                    self.select_zone_container,

                    # Selected files (replaces drop zone when files exist)
                    self.files_display,
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=40,
            expand=True,
            bgcolor=monokai_bg,
        )