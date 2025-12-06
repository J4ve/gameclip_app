"""
Arrangement Screen - Video preview & ordering (Step 2)
"""

import flet as ft
import flet_video

class ArrangementScreen:
    """Second screen: Arrange clips and preview"""
    
    def __init__(self, page=None, videos=None, on_next=None, on_back=None):
        self.page = page
        self.videos = videos or []
        self.on_next = on_next
        self.on_back = on_back
        self.main_window = None
        self.file_list = ft.Column(spacing=5)
        self.selected_video_index = 0
        self.sort_by = "Name"
        
    def build(self):
        """Build and return arrangement screen layout (Frame 2)"""
        # Update video list
        self._update_video_list()
        
        # --- LOGIC FOR PREVIEW PLAYER ---
        preview_content = None
        
        
        # Check if we have videos and a valid index
        if self.videos and 0 <= self.selected_video_index < len(self.videos):
            current_video_path = self.videos[self.selected_video_index]
            
            # Create the Flet Video Player
            # Note: volume=0.5, autoplay=False by default
            preview_content = flet_video.Video(
                playlist=[flet_video.VideoMedia(current_video_path)],
                playlist_mode=flet_video.PlaylistMode.SINGLE,
                fill_color=ft.Colors.BLACK,
                aspect_ratio=16/9,
                volume=100,
                autoplay=True,
                filter_quality=ft.FilterQuality.HIGH,
                muted=False,
            )
        else:
            # Fallback if no video is selected
            preview_content = ft.Column([
                ft.Icon(ft.Icons.VIDEO_FILE_OUTLINED, size=64, color=ft.Colors.with_opacity(0.6, "#00ACC1")),
                ft.Text(
                    "No video selected",
                    color=ft.Colors.WHITE70,
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        # --------------------------------

        # Left panel - Video list 
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
                    content=preview_content, # <--- Inserted the Player here
                    bgcolor=ft.Colors.BLACK, # Black background for video
                    border_radius=10,
                    # padding=30, # Removed padding so video fills container
                    clip_behavior=ft.ClipBehavior.HARD_EDGE, # Clips video corners to radius
                    alignment=ft.alignment.center,
                    expand=True,
                ),
                # Show filename below video
                ft.Text(
                    self.videos[self.selected_video_index].split('/')[-1] if self.videos else "",
                    color=ft.Colors.WHITE70,
                    size=12
                )
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
                # Header
                ft.Row([
                    ft.Text("Arrange Videos", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Row([
                        ft.Text("Sort by:", color=ft.Colors.WHITE70, size=14),
                        arrange_by_dropdown,
                    ]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Main content
                ft.Row([
                    video_list_panel,
                    video_preview_panel,
                ], expand=True, spacing=10),
            ], spacing=15, expand=True),
            padding=20,
            expand=True,
        )
    
    def _update_video_list(self):
        self.file_list.controls.clear()
        
        if not self.videos:
            self.file_list.controls.append(
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
                        ft.Row([
                            ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_UP, icon_color=ft.Colors.WHITE70,
                                on_click=lambda _, idx=i: self._move_video(idx, idx - 1), disabled=(i == 0)),
                            ft.IconButton(icon=ft.Icons.KEYBOARD_ARROW_DOWN, icon_color=ft.Colors.WHITE70,
                                on_click=lambda _, idx=i: self._move_video(idx, idx + 1), disabled=(i == len(self.videos) - 1)),
                            ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE, icon_color=ft.Colors.RED_400,
                                on_click=lambda _, idx=i: self._remove_video(idx)),
                        ], spacing=5),
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, "#FFFFFF") if i == self.selected_video_index else ft.Colors.with_opacity(0.02, "#FFFFFF"),
                    border_radius=8,
                    on_click=lambda _, idx=i: self._select_video(idx), # This triggers the rebuild!
                )
                self.file_list.controls.append(video_item)

    def _select_video(self, index):
        """Select a video for preview"""
        if 0 <= index < len(self.videos):
            self.selected_video_index = index
            self._update_video_list()
            # Because its calling main_window.go_to_step(1), 
            # the build() method runs again, creating a NEW ft.Video with the new path
            if self.main_window:
                self.main_window.go_to_step(1)

    def _move_video(self, from_index, to_index):
        if 0 <= to_index < len(self.videos):
            self.videos.insert(to_index, self.videos.pop(from_index))
            if self.selected_video_index == from_index:
                self.selected_video_index = to_index
            elif from_index < self.selected_video_index <= to_index:
                self.selected_video_index -= 1
            elif to_index <= self.selected_video_index < from_index:
                self.selected_video_index += 1
            self._update_video_list()
            if self.main_window:
                self.main_window.go_to_step(1)

    def _remove_video(self, index):
        if 0 <= index < len(self.videos):
            self.videos.pop(index)
            if self.selected_video_index >= len(self.videos):
                self.selected_video_index = max(0, len(self.videos) - 1)
            elif self.selected_video_index > index:
                self.selected_video_index -= 1
            self._update_video_list()
            if self.main_window:
                self.main_window.go_to_step(1)

    def _sort_videos(self, e):
        self.sort_by = e.control.value
        if self.sort_by == "Name":
            self.videos.sort(key=lambda x: x.split('/')[-1].lower() if '/' in x else x.split('\\')[-1].lower())
        self.selected_video_index = 0
        self._update_video_list()
        if self.main_window:
            self.main_window.go_to_step(1)

    def set_videos(self, videos):
        self.videos = videos or []
        self.selected_video_index = 0
        self._update_video_list()
        
        # Clear old cached preview files when videos are updated in arrangement screen
        # This ensures the SaveUploadScreen will create fresh cache for the new selection
        self._clear_preview_cache()
    
    def _clear_preview_cache(self):
        """Clear old preview cache files when videos change"""
        try:
            from pathlib import Path
            cache_dir = Path.home() / "Videos" / "VideoMerger" / ".cache"
            if cache_dir.exists():
                # Remove all preview cache files (preview_*.mp4)
                for cache_file in cache_dir.glob("preview_*.mp4"):
                    try:
                        cache_file.unlink()
                    except Exception:
                        pass  # Ignore errors, file might be in use
        except Exception:
            pass  # Ignore any errors