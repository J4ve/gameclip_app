"""
Arrangement Screen - Video preview & ordering (Step 2)
"""

import flet as ft
import flet_video
from access_control.session import session_manager
from access_control.usage_tracker import usage_tracker
import os
from datetime import datetime
from pathlib import Path
from app.video_core.video_metadata import VideoMetadata
from app.services.ad_manager import ad_manager

class ArrangementScreen:
    """Second screen: Arrange clips and preview"""
    
    def __init__(self, page=None, videos=None, on_next=None, on_back=None):
        self.page = page
        self.videos = videos or []
        self.original_order = []  # Store original order from selection
        self.arrangement_changed = False  # Track if user actually changed the order
        self.usage_recorded = False  # Track if we've already recorded usage for this session
        self.on_next = on_next
        self.on_back = on_back
        self.main_window = None
        self.file_list = ft.Column(spacing=5)
        self.selected_video_index = 0
        self.sort_by = "Name"
        self.sort_order = "Descending"  # New: Ascending/Descending
        self.locked_videos = set()  # Track locked video indices (premium feature)
        self._metadata_cache = {}  # Cache metadata to avoid repeated extraction
        self.allow_duplicates = False  # Track if duplicates are allowed
        self.change_indicator = None  # UI element to show arrangement changed status
        self.usage_info_text = None  # UI element to show usage info
        
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
        
        # Allow duplicates toggle button (hide for guests)
        duplicate_toggle = None
        if session_manager.is_authenticated:
            duplicate_toggle = ft.Container(
                content=ft.Row([
                    ft.Switch(
                        value=self.allow_duplicates,
                        active_color=ft.Colors.BLUE_400,
                        on_change=self._toggle_allow_duplicates,
                    ),
                    ft.Text("Allow Duplicates", size=14, color=ft.Colors.WHITE70),
                ], spacing=10),
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
                border_radius=5,
            )
        
        # Check if user is a guest (not authenticated)
        is_guest = not session_manager.is_authenticated
        
        # Usage info for free users
        usage_info_container = None
        if not is_guest and not (session_manager.is_premium() or session_manager.is_admin()):
            # Free user - show usage info
            usage_info = usage_tracker.get_usage_info()
            if not usage_info['unlimited']:
                self.usage_info_text = ft.Text(
                    f"Arrangements: {usage_info['used']}/{usage_info['limit']} (resets in {usage_info['reset_time']})",
                    size=12,
                    color=ft.Colors.BLUE_300 if usage_info['remaining'] > 0 else ft.Colors.RED_300,
                )
                usage_info_container = ft.Container(
                    content=self.usage_info_text,
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
                    border_radius=5,
                )
        
        # Change indicator (shows when arrangement is modified and will use a trial)
        change_text = "Arrangement modified"
        if not is_guest and not (session_manager.is_premium() or session_manager.is_admin()):
            # Free user - show trial usage warning
            change_text = "Arranged - will use 1 trial when saved"
        
        self.change_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.EDIT, size=14, color=ft.Colors.ORANGE_400),
                ft.Text(change_text, size=12, color=ft.Colors.ORANGE_400),
            ], spacing=5),
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            bgcolor=ft.Colors.with_opacity(0.15, "#FFA500"),
            border_radius=5,
            visible=False,  # Hidden by default
        )
        
        # Store the text widget reference for updates
        self.change_indicator_text = self.change_indicator.content.controls[1]
        
        # Guest lockout overlay
        guest_lockout = None
        if is_guest:
            guest_lockout = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.LOCK_OUTLINED, size=64, color=ft.Colors.AMBER_400),
                    ft.Text(
                        "Arrangement Locked",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Login to arrange your videos, change order, and use advanced features",
                        size=14,
                        color=ft.Colors.WHITE70,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Row([
                        ft.ElevatedButton(
                            "Login to Arrange",
                            icon=ft.Icons.LOGIN,
                            on_click=lambda _: self._go_back_to_login(),
                            bgcolor=ft.Colors.BLUE_700,
                            color=ft.Colors.WHITE,
                        ),
                        ft.OutlinedButton(
                            "Continue to Merge",
                            icon=ft.Icons.ARROW_FORWARD,
                            on_click=lambda _: self.main_window.next_step() if self.main_window else None,
                            style=ft.ButtonStyle(color=ft.Colors.WHITE70),
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20),
                bgcolor=ft.Colors.with_opacity(0.95, "#1A1A1A"),
                border_radius=10,
                padding=40,
                alignment=ft.alignment.center,
            )
        
        # Build header row controls
        header_controls = []
        if duplicate_toggle:
            header_controls.append(duplicate_toggle)
        if usage_info_container:
            header_controls.append(usage_info_container)
        if self.change_indicator:
            header_controls.append(self.change_indicator)
        if premium_indicator:
            header_controls.append(premium_indicator)
        
        # Add sorting controls only if not guest
        if not is_guest:
            header_controls.extend([
                ft.Text("Sort by:", color=ft.Colors.WHITE70, size=14),
                arrange_by_dropdown,
                ft.Text("Order:", color=ft.Colors.WHITE70, size=14),
                order_dropdown,
            ])
        
        # Main content - use Stack to overlay guest lockout if needed
        if is_guest:
            main_content = ft.Stack([
                ft.Row([
                    video_list_panel,
                    video_preview_panel,
                ], expand=True, spacing=10),
                guest_lockout,
            ], expand=True)
        else:
            main_content = ft.Row([
                video_list_panel,
                video_preview_panel,
            ], expand=True, spacing=10)
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Text("Arrange Videos", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Row(header_controls, spacing=10),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                # Main content
                main_content,
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
            is_guest = not session_manager.is_authenticated
            
            # Check if arrangement limit is reached for free users
            can_arrange = usage_tracker.can_arrange() if session_manager.is_authenticated else True
            self.arrangement_disabled = is_guest or not can_arrange
            
            for i, video_path in enumerate(self.videos):
                video_name = Path(video_path).name
                is_locked = i in self.locked_videos
                
                # Get metadata from cache
                if video_path not in self._metadata_cache:
                    self._metadata_cache[video_path] = VideoMetadata(video_path)
                metadata_text = self._metadata_cache[video_path].get_short_info()
                
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
                
                # Move up/down buttons (disabled for guests and limit reached)
                action_buttons.extend([
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_UP,
                        icon_color=ft.Colors.WHITE70 if (can_move_up and not self.arrangement_disabled) else ft.Colors.with_opacity(0.3, "#FFFFFF"),
                        on_click=lambda _, idx=i: self._move_video(idx, idx - 1),
                        disabled=not can_move_up or self.arrangement_disabled,
                        tooltip="Move up" if not self.arrangement_disabled else ("Login to arrange" if is_guest else "Arrangement limit reached")
                    ),
                    ft.IconButton(
                        icon=ft.Icons.KEYBOARD_ARROW_DOWN,
                        icon_color=ft.Colors.WHITE70 if (can_move_down and not self.arrangement_disabled) else ft.Colors.with_opacity(0.3, "#FFFFFF"),
                        on_click=lambda _, idx=i: self._move_video(idx, idx + 1),
                        disabled=not can_move_down or self.arrangement_disabled,
                        tooltip="Move down" if not self.arrangement_disabled else ("Login to arrange" if is_guest else "Arrangement limit reached")
                    ),
                    ft.IconButton(
                        icon=ft.Icons.COPY,
                        icon_color=ft.Colors.BLUE_400 if (self.allow_duplicates and not self.arrangement_disabled) else ft.Colors.with_opacity(0.3, "#FFFFFF"),
                        on_click=lambda _, idx=i: self._duplicate_video(idx),
                        disabled=not self.allow_duplicates or self.arrangement_disabled,
                        tooltip="Duplicate video" if not self.arrangement_disabled else ("Login to duplicate" if is_guest else "Arrangement limit reached")
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REMOVE_CIRCLE,
                        icon_color=ft.Colors.RED_400,
                        on_click=lambda _, idx=i: self._remove_video(idx),
                        tooltip="Remove video"
                    ),
                ])
                
                # Drag handle icon (shows draggability)
                drag_handle = ft.Icon(
                    ft.Icons.DRAG_INDICATOR,
                    size=20,
                    color=ft.Colors.WHITE38 if not is_locked else ft.Colors.with_opacity(0.3, "#FFFFFF"),
                )
                
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
                
                video_item_content = ft.Container(
                    content=ft.Row([
                        drag_handle,
                        index_badge,
                        ft.Column([
                            ft.Text(
                                video_name,
                                color=ft.Colors.AMBER_100 if is_locked else ft.Colors.WHITE,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                weight=ft.FontWeight.BOLD if is_locked else ft.FontWeight.NORMAL,
                                size=12,
                            ),
                            ft.Text(
                                metadata_text,
                                color=ft.Colors.AMBER_200 if is_locked else ft.Colors.GREY_400,
                                size=10,
                            ),
                        ], spacing=2, expand=True),
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
                
                # Wrap in Draggable and DragTarget for drag-and-drop reordering
                # Only allow dragging unlocked videos
                if not is_locked:
                    # Create compact feedback for drag mode
                    drag_feedback = ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.DRAG_INDICATOR, size=16, color=ft.Colors.WHITE70),
                            ft.Container(
                                content=ft.Text(str(i + 1), color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD, size=12),
                                width=24, height=24,
                                bgcolor=ft.Colors.with_opacity(0.9, "#00ACC1"),
                                border_radius=12,
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                video_name,
                                color=ft.Colors.WHITE,
                                size=12,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ], spacing=8),
                        padding=8,
                        bgcolor=ft.Colors.with_opacity(0.95, "#1A1A1A"),
                        border=ft.border.all(2, ft.Colors.BLUE_400),
                        border_radius=6,
                        width=250,
                    )
                    
                    draggable_item = ft.Draggable(
                        group="video_items",
                        content=ft.DragTarget(
                            group="video_items",
                            content=video_item_content,
                            on_accept=lambda e, idx=i: self._handle_drag_accept(e, idx),
                            on_will_accept=lambda e, idx=i: self._handle_drag_will_accept(e, idx),
                            on_leave=lambda e, idx=i: self._handle_drag_leave(e, idx),
                        ),
                        content_feedback=drag_feedback,
                        data=i,
                    )
                    self.file_list.controls.append(draggable_item)
                else:
                    # Locked videos can only be drop targets (can't be dragged)
                    drag_target_item = ft.DragTarget(
                        group="video_items",
                        content=video_item_content,
                        on_accept=lambda e, idx=i: self._handle_drag_accept(e, idx),
                        on_will_accept=lambda e, idx=i: self._handle_drag_will_accept(e, idx),
                        on_leave=lambda e, idx=i: self._handle_drag_leave(e, idx),
                    )
                    self.file_list.controls.append(drag_target_item)

    def _select_video(self, index):
        """Select a video for preview"""
        if 0 <= index < len(self.videos):
            self.selected_video_index = index
            self._update_video_list()
            # Because its calling main_window.go_to_step(1), 
            # the build() method runs again, creating a NEW ft.Video with the new path
            if self.main_window:
                self.main_window.go_to_step(1)
    
    def _handle_drag_accept(self, e, target_idx):
        """Handle when a video is dropped on another video"""
        # Check if user has permission to arrange
        if self.arrangement_disabled:
            # Show feedback to user
            if session_manager.is_guest:
                message = "⚠️ Login to arrange videos"
                color = ft.Colors.AMBER_700
            else:
                message = "⚠️ Arrangement limit reached. Resets at midnight UTC."
                color = ft.Colors.RED_400
            
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(message, color=ft.Colors.WHITE),
                    bgcolor=color
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        source_idx = e.src_id if hasattr(e, 'src_id') else e.data
        
        # Get the actual source index from the draggable's data
        if hasattr(e.control.page, 'get_control'):
            src_control = e.control.page.get_control(e.src_id)
            if src_control and hasattr(src_control, 'data'):
                source_idx = src_control.data
        
        # Don't move if source and target are the same
        if source_idx == target_idx:
            return
        
        # Don't allow dropping on locked positions
        if target_idx in self.locked_videos:
            return
        
        # Don't allow moving locked videos
        if source_idx in self.locked_videos:
            return
        
        # Perform the move
        self._move_video(source_idx, target_idx)
    
    def _handle_drag_will_accept(self, e, target_idx):
        """Visual feedback when hovering over a drop target"""
        # Check if user has permission to arrange
        if self.arrangement_disabled:
            # Show red border - not allowed
            e.control.content.border = ft.border.all(2, ft.Colors.RED_400)
        # Check if drop is allowed
        elif target_idx in self.locked_videos:
            # Locked position - show red border
            e.control.content.border = ft.border.all(2, ft.Colors.RED_400)
        else:
            # Valid drop position - show green border
            e.control.content.border = ft.border.all(2, ft.Colors.GREEN_400)
        
        if self.page:
            self.page.update()
    
    def _handle_drag_leave(self, e, target_idx):
        """Remove visual feedback when drag leaves the target"""
        is_locked = target_idx in self.locked_videos
        # Restore original border
        e.control.content.border = ft.border.all(1, ft.Colors.AMBER_700) if is_locked else None
        
        if self.page:
            self.page.update()

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
        self._update_change_indicator()  # Check if arrangement changed
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
            self._update_change_indicator()  # Check if arrangement changed
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
        self._update_change_indicator()  # Check if arrangement changed
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
    
    def _duplicate_video(self, index):
        """Duplicate a video entry at the next position"""
        if not self.allow_duplicates:
            return
        
        if 0 <= index < len(self.videos):
            # Get the video path to duplicate
            video_path = self.videos[index]
            
            # Insert duplicate right after the original
            self.videos.insert(index + 1, video_path)
            
            # Update locked positions for indices after the insertion point
            new_locked = set()
            for locked_idx in self.locked_videos:
                if locked_idx > index:
                    new_locked.add(locked_idx + 1)
                else:
                    new_locked.add(locked_idx)
            self.locked_videos = new_locked
            
            # Update selected index if needed
            if self.selected_video_index > index:
                self.selected_video_index += 1
            
            # Show success message
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Duplicated: {Path(video_path).name}"),
                    bgcolor=ft.Colors.GREEN_700
                )
                self.page.snack_bar.open = True
            
            self._update_video_list()
            self._update_change_indicator()  # Check if arrangement changed
            if self.main_window:
                self.main_window.go_to_step(1)
    
    def _toggle_allow_duplicates(self, e):
        """Toggle the allow duplicates setting"""
        self.allow_duplicates = e.control.value
        
        # If duplicates are being disabled, remove existing duplicates
        if not self.allow_duplicates:
            self._remove_duplicates()
        
        self._update_video_list()
        self._update_change_indicator()  # Check if arrangement changed
        if self.main_window:
            self.main_window.go_to_step(1)
    
    def _remove_duplicates(self):
        """Remove duplicate video entries when duplicates are disabled"""
        if not self.videos:
            return
        
        seen_paths = set()
        indices_to_remove = []
        
        # Find duplicate indices (keep first occurrence)
        for i, video_path in enumerate(self.videos):
            if video_path in seen_paths:
                indices_to_remove.append(i)
            else:
                seen_paths.add(video_path)
        
        # Remove duplicates in reverse order to maintain indices
        removed_count = 0
        for idx in reversed(indices_to_remove):
            self.videos.pop(idx)
            removed_count += 1
            
            # Update locked positions
            new_locked = set()
            for locked_idx in self.locked_videos:
                if locked_idx < idx:
                    new_locked.add(locked_idx)
                elif locked_idx > idx:
                    new_locked.add(locked_idx - 1)
            self.locked_videos = new_locked
            
            # Update selected index
            if self.selected_video_index >= len(self.videos) and len(self.videos) > 0:
                self.selected_video_index = len(self.videos) - 1
            elif self.selected_video_index > idx:
                self.selected_video_index -= 1
        
        # Show message if duplicates were removed
        if removed_count > 0 and self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Removed {removed_count} duplicate {'entry' if removed_count == 1 else 'entries'}"),
                bgcolor=ft.Colors.ORANGE_700
            )
            self.page.snack_bar.open = True

    def set_videos(self, videos):
        self.videos = videos or []
        self.original_order = videos.copy() if videos else []  # Save original order
        self.arrangement_changed = False  # Reset change flag
        self.usage_recorded = False  # Reset usage tracking
        self.selected_video_index = 0
        self.locked_videos.clear()  # Clear locks when new videos are loaded
        self._metadata_cache.clear()  # Clear metadata cache for new video set
        
        # Pre-cache metadata for all videos (done once, in background if needed)
        for video_path in self.videos:
            if video_path not in self._metadata_cache:
                self._metadata_cache[video_path] = VideoMetadata(video_path)
        
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
    
    def _check_arrangement_changed(self):
        """Check if the current arrangement differs from original order"""
        if len(self.videos) != len(self.original_order):
            return True
        
        for i, video in enumerate(self.videos):
            if video != self.original_order[i]:
                return True
        
        return False
    
    def _update_change_indicator(self):
        """Update the change indicator visibility based on arrangement status"""
        if self.change_indicator:
            changed = self._check_arrangement_changed()
            
            # Update arrangement_changed flag
            self.arrangement_changed = changed
            
            # Show/hide indicator based on whether arrangement differs from original
            self.change_indicator.visible = changed
            
            # Update text for free users to show trial usage warning
            if changed and self.change_indicator_text:
                is_guest = not session_manager.is_authenticated
                if not is_guest and not (session_manager.is_premium() or session_manager.is_admin()):
                    # Free user - show trial warning
                    usage_info = usage_tracker.get_usage_info()
                    if usage_info and not usage_info['unlimited']:
                        remaining = usage_info['remaining']
                        self.change_indicator_text.value = f"Arranged - will use 1 trial when saved ({remaining} left)"
                else:
                    # Premium/Admin/Guest
                    self.change_indicator_text.value = "Arrangement modified"
            
            if self.page:
                self.page.update()
    
    def _go_back_to_login(self):
        """Navigate back to start and trigger login"""
        if self.main_window:
            self.main_window.go_to_step(0)  # Go back to selection screen
            # The user can then click login from the selection screen
    
    def record_arrangement_usage(self) -> bool:
        """Record arrangement usage when user proceeds to next step (saves)"""
        # Only record if arrangement was actually changed
        if not self._check_arrangement_changed():
            print("Arrangement unchanged - no usage recorded")
            return True  # Return true to allow proceeding
        
        # Don't record for premium/admin
        if session_manager.is_premium() or session_manager.is_admin():
            return True
        
        # Don't record for guests
        if not session_manager.is_authenticated:
            return True
        
        # Check if user can still arrange before recording
        if not usage_tracker.can_arrange():
            print("Arrangement limit reached - cannot proceed")
            return False
        
        # Record usage for free users
        if not self.usage_recorded:
            if usage_tracker.record_arrangement():
                self.usage_recorded = True
                print("Arrangement usage recorded")
                
                # Update usage info display
                if self.usage_info_text:
                    usage_info = usage_tracker.get_usage_info()
                    if not usage_info['unlimited']:
                        self.usage_info_text.value = f"Arrangements: {usage_info['used']}/{usage_info['limit']} (resets in {usage_info['reset_time']})"
                        self.usage_info_text.color = ft.Colors.BLUE_300 if usage_info['remaining'] > 0 else ft.Colors.RED_300
                        if self.page:
                            self.page.update()
                return True
            else:
                # Limit reached
                print("Arrangement limit reached - cannot proceed")
                return False
        
        return True
    
    def _show_premium_coming_soon(self):
        """Show coming soon message for premium feature"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Premium subscription coming soon! 🚀"),
                bgcolor=ft.Colors.AMBER_700
            )
            self.page.snack_bar.open = True
            self.page.update()