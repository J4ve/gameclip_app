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
        self.main_window = None  # Will be set when built
        self.file_list = ft.Column(spacing=5)
        self.selected_video_index = 0
        self.playback_position = 0
        self.is_playing = False
        self.sort_by = "Name"  # Default sort option
        
    def build(self):
        """Build and return arrangement screen layout (Frame 2)"""
        # Update video list
        self._update_video_list()
        
        # Left panel - Video list with reorder controls
        video_list_panel = ft.Container(
            content=ft.Column([
                ft.Text("Video List", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(
                    content=ft.Column(
                        [self.file_list], 
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    expand=True,
                ),
            ]),
            width=400,
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=10,
            margin=ft.margin.only(right=10),
        )
        
        # Center - Video preview area
        video_preview_panel = ft.Container(
            content=ft.Column([
                ft.Text("Video Preview", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.VIDEO_FILE_OUTLINED, size=64, color=ft.Colors.with_opacity(0.6, "#00ACC1")),
                        ft.Text(
                            self.videos[self.selected_video_index].split('/')[-1] if self.videos and self.selected_video_index < len(self.videos) else "No video selected",
                            color=ft.Colors.WHITE70,
                            size=14,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    bgcolor=ft.Colors.with_opacity(0.05, "#000000"),
                    border_radius=10,
                    padding=30,
                    alignment=ft.alignment.center,
                    expand=True,
                ),
            ]),
            expand=True,
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=10,
        )
        
        # Top right - "Arrange By" dropdown
        arrange_by_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Name"),
                ft.dropdown.Option("Date"),
                ft.dropdown.Option("Size"),
                ft.dropdown.Option("Custom"),
            ],
            value=self.sort_by,
            on_change=self._sort_videos,
            width=150,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
        )
        
        return ft.Container(
            content=ft.Column([
                # Header with title and sort dropdown
                ft.Row([
                    ft.Text("Arrange Videos", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Row([
                        ft.Text("Sort by:", color=ft.Colors.WHITE70, size=14),
                        arrange_by_dropdown,
                    ]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Main content area
                ft.Row([
                    video_list_panel,
                    video_preview_panel,
                ], expand=True, spacing=10),
            ], spacing=15, expand=True),
            padding=20,
            expand=True,
        )
    
    def _update_video_list(self):
        """Update the video list display"""
        self.file_list.controls.clear()
        
        if not self.videos:
            self.file_list.controls.append(
                ft.Text(
                    "No videos selected. Go back to select videos.",
                    color=ft.Colors.WHITE70,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        else:
            for i, video_path in enumerate(self.videos):
                video_name = video_path.split('/')[-1] if '/' in video_path else video_path.split('\\')[-1]
                
                video_item = ft.Container(
                    content=ft.Row([
                        # Video number
                        ft.Container(
                            content=ft.Text(str(i + 1), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            width=30,
                            height=30,
                            bgcolor=ft.Colors.with_opacity(0.8, "#00ACC1"),
                            border_radius=15,
                            alignment=ft.alignment.center,
                        ),
                        
                        # Video name
                        ft.Text(
                            video_name,
                            color=ft.Colors.WHITE,
                            expand=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        
                        # Control buttons
                        ft.Row([
                            ft.IconButton(
                                icon=ft.Icons.KEYBOARD_ARROW_UP,
                                icon_color=ft.Colors.WHITE70,
                                tooltip="Move up",
                                on_click=lambda _, idx=i: self._move_video(idx, idx - 1),
                                disabled=(i == 0),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                                icon_color=ft.Colors.WHITE70,
                                tooltip="Move down",
                                on_click=lambda _, idx=i: self._move_video(idx, idx + 1),
                                disabled=(i == len(self.videos) - 1),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REMOVE_CIRCLE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="Remove video",
                                on_click=lambda _, idx=i: self._remove_video(idx),
                            ),
                        ], spacing=5),
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, "#FFFFFF") if i == self.selected_video_index else ft.Colors.with_opacity(0.02, "#FFFFFF"),
                    border_radius=8,
                    on_click=lambda _, idx=i: self._select_video(idx),
                )
                
                self.file_list.controls.append(video_item)
    
    def _select_video(self, index):
        """Select a video for preview"""
        if 0 <= index < len(self.videos):
            self.selected_video_index = index
            self._update_video_list()  # Refresh to show selection
            # Update UI through main window
            if self.main_window:
                self.main_window.go_to_step(1)  # Rebuild current step
    
    def _move_video(self, from_index, to_index):
        """Move video in the list"""
        if 0 <= to_index < len(self.videos):
            self.videos.insert(to_index, self.videos.pop(from_index))
            if self.selected_video_index == from_index:
                self.selected_video_index = to_index
            elif from_index < self.selected_video_index <= to_index:
                self.selected_video_index -= 1
            elif to_index <= self.selected_video_index < from_index:
                self.selected_video_index += 1
            self._update_video_list()
            # Update UI through main window
            if self.main_window:
                self.main_window.go_to_step(1)  # Rebuild current step
    
    def _remove_video(self, index):
        """Remove video from the list"""
        if 0 <= index < len(self.videos):
            self.videos.pop(index)
            if self.selected_video_index >= len(self.videos):
                self.selected_video_index = max(0, len(self.videos) - 1)
            elif self.selected_video_index > index:
                self.selected_video_index -= 1
            self._update_video_list()
            # Update UI through main window
            if self.main_window:
                self.main_window.go_to_step(1)  # Rebuild current step
    
    def _sort_videos(self, e):
        """Sort videos by selected criteria"""
        self.sort_by = e.control.value
        if self.sort_by == "Name":
            self.videos.sort(key=lambda x: x.split('/')[-1].lower() if '/' in x else x.split('\\')[-1].lower())
        elif self.sort_by == "Size":
            # Note: This would require actual file size checking
            pass
        elif self.sort_by == "Date":
            # Note: This would require actual file date checking
            pass
        # Custom would keep current order
        self.selected_video_index = 0
        self._update_video_list()
        # Update UI through main window
        if self.main_window:
            self.main_window.go_to_step(1)  # Rebuild current step
    
    def set_videos(self, videos):
        """Set videos from selection screen"""
        self.videos = videos or []
        self.selected_video_index = 0
        self._update_video_list()
