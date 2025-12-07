"""
Arrangement Screen - Video preview & ordering (Step 2)
"""

import flet as ft
import flet_video
from access_control.session import session_manager
import os
from datetime import datetime

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
        self.sort_order = "Descending"  # New: Ascending/Descending
        self.locked_videos = set()  # Track locked video indices (premium feature)
        
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
                ft.dropdown.Option("Date Modified"),
                ft.dropdown.Option("Date Created"),
                ft.dropdown.Option("Size"),
                ft.dropdown.Option("Custom"),
            ],
            value=self.sort_by,
            on_change=self._sort_videos,
            width=180,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
        )
        order_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("Ascending"),
                ft.dropdown.Option("Descending"),
            ],
            value=self.sort_order,
            on_change=self._change_sort_order,
            width=120,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            text_style=ft.TextStyle(color=ft.Colors.WHITE),
        )
        
        # Premium feature indicator
        premium_indicator = None
        if session_manager.is_premium() or session_manager.is_admin():
            premium_indicator = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LOCK, size=14, color=ft.Colors.AMBER_400),
                    ft.Text("Lock enabled", size=12, color=ft.Colors.AMBER_400, weight=ft.FontWeight.BOLD),
                ], spacing=5),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.with_opacity(0.15, "#FFA500"),
                border_radius=5,
            )
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text("Arrange Videos", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Row([
                        premium_indicator if premium_indicator else ft.Container(),
                        ft.Text("Sort by:", color=ft.Colors.WHITE70, size=14),
                        arrange_by_dropdown,
                        ft.Text("Order:", color=ft.Colors.WHITE70, size=14),
                        order_dropdown,
                    ], spacing=10),
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
            # Check if user has premium/admin access
            has_lock_feature = session_manager.is_premium() or session_manager.is_admin()
            
            for i, video_path in enumerate(self.videos):
                video_name = video_path.split('/')[-1] if '/' in video_path else video_path.split('\\')[-1]
                is_locked = i in self.locked_videos
                
                # Determine if move buttons should be enabled
                can_move_up = i > 0 and not is_locked
                can_move_down = i < len(self.videos) - 1 and not is_locked
                
                # Build action buttons
                action_buttons = []
                
                # Lock/unlock button (premium feature)
                if has_lock_feature:
                    lock_button = ft.IconButton(
                        icon=ft.Icons.LOCK if is_locked else ft.Icons.LOCK_OPEN,
                        icon_color=ft.Colors.AMBER_400 if is_locked else ft.Colors.WHITE54,
                        tooltip="Unlock position" if is_locked else "Lock position",
                        on_click=lambda _, idx=i: self._toggle_lock(idx),
                    )
                    action_buttons.append(lock_button)
                
                # Move up/down buttons
                action_buttons.extend([
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_UP,
                        icon_color=ft.Colors.WHITE70 if can_move_up else ft.Colors.with_opacity(0.3, "#FFFFFF"),
                        on_click=lambda _, idx=i: self._move_video(idx, idx - 1),
                        disabled=not can_move_up,
                        tooltip="Move up"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                        icon_color=ft.Colors.WHITE70 if can_move_down else ft.Colors.with_opacity(0.3, "#FFFFFF"),
                        on_click=lambda _, idx=i: self._move_video(idx, idx + 1),
                        disabled=not can_move_down,
                        tooltip="Move down"
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_CIRCLE,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda _, idx=i: self._remove_video(idx),
                        tooltip="Remove video"
                    ),
                ])
                
                # Index badge with lock indicator (centered)
                if is_locked:
                    index_badge = ft.Container(
                        content=ft.Row([
                            ft.Text(str(i + 1), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                            ft.Icon(ft.Icons.LOCK, size=12, color=ft.Colors.AMBER_400),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=2),
                        width=30, height=30,
                        bgcolor=ft.Colors.AMBER_700,
                        border_radius=15,
                        alignment=ft.alignment.center,
                    )
                else:
                    index_badge = ft.Container(
                        content=ft.Text(str(i + 1), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                        width=30, height=30,
                        bgcolor=ft.Colors.with_opacity(0.8, "#00ACC1"),
                        border_radius=15,
                        alignment=ft.alignment.center,
                    )
                
                video_item = ft.Container(
                    content=ft.Row([
                        index_badge,
                        ft.Text(
                            video_name,
                            color=ft.Colors.AMBER_100 if is_locked else ft.Colors.WHITE,
                            expand=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                            weight=ft.FontWeight.BOLD if is_locked else ft.FontWeight.NORMAL,
                        ),
                        ft.Row(action_buttons, spacing=5),
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.08, "#FFA500") if is_locked else (
                        ft.Colors.with_opacity(0.05, "#FFFFFF") if i == self.selected_video_index else ft.Colors.with_opacity(0.02, "#FFFFFF")
                    ),
                    border=ft.border.all(1, ft.Colors.AMBER_700) if is_locked else None,
                    border_radius=8,
                    on_click=lambda _, idx=i: self._select_video(idx),
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
        """Move video with respect to locked positions"""
        if not (0 <= to_index < len(self.videos)):
            return
        
        # Don't allow moving locked videos
        if from_index in self.locked_videos:
            return
        
        # Don't allow moving to a locked position
        if to_index in self.locked_videos:
            return
        
        # Perform the move
        video = self.videos.pop(from_index)
        self.videos.insert(to_index, video)
        
        # Update locked positions
        new_locked = set()
        for locked_idx in self.locked_videos:
            if locked_idx == from_index:
                continue  # This shouldn't happen, but skip if it does
            elif from_index < locked_idx <= to_index:
                new_locked.add(locked_idx - 1)
            elif to_index <= locked_idx < from_index:
                new_locked.add(locked_idx + 1)
            else:
                new_locked.add(locked_idx)
        self.locked_videos = new_locked
        
        # Update selected video index
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
        """Remove video and update locked positions"""
        if 0 <= index < len(self.videos):
            self.videos.pop(index)
            
            # Update locked positions
            new_locked = set()
            for locked_idx in self.locked_videos:
                if locked_idx < index:
                    new_locked.add(locked_idx)
                elif locked_idx > index:
                    new_locked.add(locked_idx - 1)
                # Skip if locked_idx == index (we're removing it)
            self.locked_videos = new_locked
            
            # Update selected index
            if self.selected_video_index >= len(self.videos):
                self.selected_video_index = max(0, len(self.videos) - 1)
            elif self.selected_video_index > index:
                self.selected_video_index -= 1
            
            self._update_video_list()
            if self.main_window:
                self.main_window.go_to_step(1)

    def _sort_videos(self, e):
        """Sort videos while respecting locked positions"""
        self.sort_by = e.control.value
        self._apply_sort()

    def _change_sort_order(self, e):
        self.sort_order = e.control.value
        self._apply_sort()

    def _apply_sort(self):
        if self.sort_by == "Custom":
            # Custom sorting - no automatic sorting
            self._update_video_list()
            if self.main_window:
                self.main_window.go_to_step(1)
            return

        # Separate locked and unlocked videos with their original indices
        locked_items = [(i, self.videos[i]) for i in self.locked_videos]
        unlocked_indices = [i for i in range(len(self.videos)) if i not in self.locked_videos]
        unlocked_items = [(i, self.videos[i]) for i in unlocked_indices]

        # Determine sort direction
        reverse = self.sort_order == "Descending"

        # Sort unlocked videos based on selected criteria
        if self.sort_by == "Name":
            unlocked_items.sort(key=lambda x: os.path.basename(x[1]).lower(), reverse=reverse)
        elif self.sort_by == "Date Modified":
            try:
                unlocked_items.sort(key=lambda x: os.path.getmtime(x[1]), reverse=reverse)
            except:
                unlocked_items.sort(key=lambda x: os.path.basename(x[1]).lower(), reverse=reverse)
        elif self.sort_by == "Date Created":
            try:
                unlocked_items.sort(key=lambda x: os.path.getctime(x[1]), reverse=reverse)
            except:
                unlocked_items.sort(key=lambda x: os.path.basename(x[1]).lower(), reverse=reverse)
        elif self.sort_by == "Size":
            try:
                unlocked_items.sort(key=lambda x: os.path.getsize(x[1]), reverse=reverse)
            except:
                unlocked_items.sort(key=lambda x: os.path.basename(x[1]).lower(), reverse=reverse)

        # Rebuild video list, placing locked videos back in their positions
        new_videos = [None] * len(self.videos)
        new_locked = set()

        # Place locked videos first
        for orig_idx, video in locked_items:
            new_videos[orig_idx] = video
            new_locked.add(orig_idx)

        # Fill remaining positions with sorted unlocked videos
        unlocked_videos = [video for _, video in unlocked_items]
        unlocked_idx = 0
        for i in range(len(new_videos)):
            if new_videos[i] is None:
                new_videos[i] = unlocked_videos[unlocked_idx]
                unlocked_idx += 1

        self.videos = new_videos
        self.locked_videos = new_locked
        self.selected_video_index = 0

        self._update_video_list()
        if self.main_window:
            self.main_window.go_to_step(1)
    
    def _toggle_lock(self, index):
        """Toggle lock state for a video (premium feature)"""
        # Security check - only premium/admin users can lock
        if not (session_manager.is_premium() or session_manager.is_admin()):
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Lock feature is available for Premium and Admin users only"),
                    bgcolor=ft.Colors.ORANGE_700
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        if index in self.locked_videos:
            self.locked_videos.remove(index)
        else:
            self.locked_videos.add(index)
        
        self._update_video_list()
        if self.main_window:
            self.main_window.go_to_step(1)

    def set_videos(self, videos):
        self.videos = videos or []
        self.selected_video_index = 0
        self.locked_videos.clear()  # Clear locks when new videos are loaded
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