"""
Save/Upload Screen - Final configuration & upload (Step 3)
"""

import flet as ft
from configs.config import Config
from datetime import datetime
from pathlib import Path
import sys
import os
from access_control.session import session_manager
from app.services.ads_manager import should_show_ads, get_banner_ad

# Add src/ to sys.path so we can import uploader modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))



class SaveUploadScreen:
    """Third screen: Configure output and upload settings"""
    
    def __init__(self, videos=None, page=None, on_save=None, on_upload=None, on_back=None):
        self.page = page
        self.videos = videos or []
        self.on_save = on_save
        self.on_upload = on_upload
        self.on_back = on_back
        self.main_window = None
        self.file_list = ft.Column(spacing=5)
        
        # Video processor will be imported when needed
        self.video_processor = None
        
        # Form fields
        self.filename_field = None
        self.format_dropdown = None
        self.codec_dropdown = None
        self.title_field = None
        self.tags_field = None
        self.visibility_dropdown = None
        self.description_field = None
        self.made_for_kids_checkbox = None
        
        # Progress tracking
        self.progress_bar = None
        self.progress_text = None
        self.save_button = None
        self.upload_button = None
        self.cancel_button = None
        
        # Preview
        self.preview_container = None
        self.preview_video = None
        
        # Cached merged video (preview)
        self.cached_preview_path = None
        self.is_merging_preview = False
        
        # YouTube upload
        self.youtube_service = None
        self.merged_video_path = None
        self.is_uploading = False
        
        # Output paths
        self.output_directory = str(Path.home() / "Videos" / "VideoMerger")
        self.cache_directory = str(Path.home() / "Videos" / "VideoMerger" / ".cache")
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        Path(self.cache_directory).mkdir(parents=True, exist_ok=True)


        # Preview text label
        self.preview_text_label = ft.Text(
            "Preview will appear when ready",
            color=ft.Colors.GREY_400,
            size=12,
        )

    def _get_role_display_text(self, role_name: str) -> str:
        """Get user-friendly role display text"""
        role_lower = role_name.lower()
        if role_lower == 'free':
            return "Free tier user"
        elif role_lower == 'guest':
            return "Guest user"
        elif role_lower == 'premium':
            return "Premium user"
        elif role_lower == 'admin':
            return "Administrator account"
        else:
            return f"{role_name.title()} user"

    def set_videos(self, videos):
        """Set videos and trigger preview merge"""
        self.videos = videos or []
        
        # Clear old cached preview files when new videos are selected
        if self.video_processor is not None:
            self.video_processor.cache_processor.clear_all_cache()
        
        # Also manually clean up any leftover cache files from the cache directory
        self._clean_cache_directory()
        
        if self.videos and not self.is_merging_preview:
            self._merge_preview()
        
    def _clean_cache_directory(self):
        """Clean up old cache files from the cache directory"""
        try:
            cache_dir = Path(self.cache_directory)
            if cache_dir.exists():
                # Remove all preview cache files (preview_*.mp4)
                for cache_file in cache_dir.glob("preview_*.mp4"):
                    try:
                        cache_file.unlink()
                    except Exception:
                        pass  # Ignore errors, file might be in use
        except Exception:
            pass  # Ignore directory errors
        
    def _initialize_video_processor(self):
        """Lazy load video processor"""
        if self.video_processor is None:
            from app.video_core.video_processor import VideoProcessor
            self.video_processor = VideoProcessor()
            
            # Check FFmpeg availability
            if not self.video_processor.check_ffmpeg():
                self._show_error("FFmpeg not found. Please install FFmpeg to merge videos.")
                return False
        return True
    
    def _merge_preview(self):
        """Merge videos for preview (cached in background with downscaling)"""
        if not self.videos:
            return
        
        self.is_merging_preview = True
        
        # Initialize processor
        if not self._initialize_video_processor():
            self.is_merging_preview = False
            return
        
        # Create cache filename with timestamp
        cache_filename = f"preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cache_path = str(Path(self.cache_directory) / cache_filename)
        
        # Show merging status
        if self.progress_text:
            self.progress_text.value = "Creating preview..."
            self.progress_text.visible = True
        if self.progress_bar:
            self.progress_bar.visible = True
        if self.page:
            self.page.update()
        
        # Start merge using cache processor (with downscaling)
        self.video_processor.merge_and_cache(
            video_paths=self.videos,
            cache_path=cache_path,
            progress_callback=self._update_preview_progress,
            completion_callback=self._preview_merge_complete
        )

    def _update_preview_progress(self, percentage: int, message: str):
        """Update progress for preview merge"""
        if self.progress_text:
            self.preview_text_label.value = f"Preview: {message}"
        if self.page:
            self.page.update()
    
    def _preview_merge_complete(self, success: bool, message: str, output_path: str):
        """Handle preview merge completion - display the cached video"""
        self.is_merging_preview = False
        
        if success and output_path:
            self.cached_preview_path = output_path
            # Check if cache file exists before trying to display
            if Path(output_path).exists():
                self._show_preview_video(output_path)
            else:
                if self.progress_text:
                    self.progress_text.value = "Preview file created but not accessible"
                    self.progress_text.visible = False
        else:
            if self.progress_text:
                self.progress_text.value = "Preview unavailable"
                self.progress_text.visible = False
        
        # Hide progress
        if self.progress_bar:
            self.progress_bar.visible = False
        if self.page:
            self.page.update()
    
    def _monitor_cache_file(self, cache_path: str, check_interval: float = 2.0):
        """Monitor cache file and update preview once it has content"""
        last_size = 0
        min_file_size = 500000  # 500KB minimum before showing preview
        
        while self.is_merging_preview:
            try:
                if Path(cache_path).exists():
                    current_size = Path(cache_path).stat().st_size
                    
                    # Update preview once file is large enough
                    if current_size > min_file_size and current_size > last_size:
                        # Only update preview if it hasn't been set yet
                        if not self.cached_preview_path:
                            self.cached_preview_path = cache_path
                            self._show_preview_video(cache_path)
                    
                    last_size = current_size
            except Exception:
                pass
    
    def _show_preview_video(self, video_path: str):
        """Display the preview video"""
        if not self.preview_container:
            return
        
        # Create video player
        self.preview_video = ft.Video(
            playlist=[ft.VideoMedia(video_path)],
            playlist_mode=ft.PlaylistMode.LOOP,
            fill_color=ft.Colors.BLACK,
            aspect_ratio=16/9,
            volume=50,
            autoplay=True,
            filter_quality=ft.FilterQuality.HIGH,
            muted=False,
        )
        
        # Update container
        self.preview_container.content = self.preview_video
        if self.page:
            self.page.update()

        self.preview_text_label.visible = False
        
    def build(self):
        """Build and return save/upload screen layout"""
        
        # Generate default filename with timestamp
        default_filename = f"merged_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save Settings section
        self.filename_field = ft.TextField(
            label="Filename",
            value=default_filename,
            expand=True
        )
        
        self.format_dropdown = ft.Dropdown(
            label="File Type",
            options=[ft.dropdown.Option(fmt) for fmt in Config.SUPPORTED_VIDEO_FORMATS],
            value=Config.DEFAULT_VIDEO_FORMAT,
            width=150,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREY_900,
        )
        
        self.codec_dropdown = ft.Dropdown(
            label="Codec",
            options=[ft.dropdown.Option(codec) for codec in Config.SUPPORTED_CODECS],
            value=Config.DEFAULT_CODEC,
            width=150,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREY_900,
        )
        
        # Output directory selection
        output_dir_field = ft.TextField(
            label="Output Directory",
            value=self.output_directory,
            read_only=True,
            expand=True
        )
        
        browse_dir_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OPEN,
            tooltip="Choose output directory",
            on_click=self._browse_output_directory
        )
        
        save_settings_section = ft.Column([
            ft.Text("Save Settings", size=16, weight=ft.FontWeight.BOLD),
            self.filename_field,
            ft.Row([self.format_dropdown, self.codec_dropdown], spacing=10),
            ft.Row([output_dir_field, browse_dir_button], spacing=5),
        ], spacing=10)

        # Upload Settings section
        self.title_field = ft.TextField(label="Title", value=default_filename)
        self.tags_field = ft.TextField(label="Tags (comma separated)")
        self.visibility_dropdown = ft.Dropdown(
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
        )
        self.description_field = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        self.made_for_kids_checkbox = ft.Checkbox(
            label="This video is made for kids (COPPA)",
            value=False
        )
        
        # Upload Settings section - role-based restrictions
        upload_enabled = session_manager.can_upload()
        upload_status_text = ""
        
        if not upload_enabled:
            if session_manager.is_guest:
                upload_status_text = "⚠️ Guest users cannot upload. Login with Google to enable uploads."
            else:
                upload_status_text = "⚠️ Your account does not have upload permissions."
        
        # Build upload settings section - hide form fields for guests
        upload_section_controls = [
            ft.Text("Upload Settings", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Configure metadata for YouTube upload", size=12, color=ft.Colors.GREY_400),
            ft.Text(upload_status_text, size=11, color=ft.Colors.ORANGE_400, visible=not upload_enabled),
        ]
        
        # Only show upload form fields if user can upload
        if upload_enabled:
            upload_section_controls.extend([
                ft.ElevatedButton(
                    "Edit Upload Settings",
                    icon=ft.Icons.EDIT,
                    on_click=self._open_upload_settings_dialog,
                    disabled=not upload_enabled
                ),
            ])
        else:
            # Show a message for guests instead
            upload_section_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.LOCK, size=32, color=ft.Colors.ORANGE_400),
                        ft.Text(
                            "Create a free account and sign in to enable YouTube uploads.",
                            size=12,
                            color=ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=15,
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.1, "#FF9800"),
                )
            )
        
        upload_settings_section = ft.Column(upload_section_controls, spacing=10)

        # Progress section
        self.progress_bar = ft.ProgressBar(
            value=0,
            color=ft.Colors.with_opacity(0.9, "#00897B"),
            bgcolor=ft.Colors.with_opacity(0.3, "#37474F"),
            visible=False,
            height=8
        )
        
        self.progress_text = ft.Text(
            "",
            size=12,
            color=ft.Colors.WHITE70,
            visible=False
        )
        
        progress_section = ft.Column([
            self.progress_bar,
            self.progress_text,
        ], spacing=5)

        # Buttons section - with role-based restrictions
        save_enabled = session_manager.can_save()
        upload_enabled = session_manager.can_upload()
        is_guest = session_manager.is_guest
        
        # Add watermark warning for guests
        watermark_warning = ""
        if session_manager.has_watermark():
            watermark_warning = "⚠️ Guest videos include watermark"
        
        # Determine save button text and tooltip
        save_button_text = "Save Video"
        save_button_tooltip = "Save merged video locally"
        if is_guest:
            save_button_tooltip = "Save merged video locally (guest users)"
        
        self.save_button = ft.ElevatedButton(
            save_button_text,
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.with_opacity(0.85, "#00897B"),
            color=ft.Colors.WHITE,
            on_click=self._handle_save,
            height=45,
            width=150,
            disabled=not save_enabled,
            tooltip=save_button_tooltip,
        )
        
        upload_button_text = "Save & Upload" if upload_enabled else "Upload Disabled"
        upload_button_tooltip = "Save and upload to YouTube" if upload_enabled else "Upgrade to upload videos"
        self.upload_button = ft.ElevatedButton(
            upload_button_text,
            icon=ft.Icons.UPLOAD if upload_enabled else ft.Icons.LOCK,
            bgcolor=ft.Colors.with_opacity(0.85, "#1976D2") if upload_enabled else ft.Colors.with_opacity(0.5, "#666666"),
            color=ft.Colors.WHITE,
            on_click=self._handle_upload,
            height=45,
            width=150,
            disabled=not upload_enabled,
            tooltip=upload_button_tooltip,
        )
        
        self.cancel_button = ft.ElevatedButton(
            "Cancel",
            icon=ft.Icons.CANCEL,
            bgcolor=ft.Colors.with_opacity(0.85, "#D32F2F"),
            color=ft.Colors.WHITE,
            on_click=self._handle_cancel,
            height=45,
            width=150,
            visible=False
        )
        
        # Role info section
        role_display = self._get_role_display_text(session_manager.role_name)
        role_color = ft.Colors.ORANGE_400 if session_manager.is_guest else ft.Colors.CYAN_400
        
        role_info_controls = [
            ft.Text(
                role_display,
                size=12,
                weight=ft.FontWeight.W_500,
                color=role_color
            ),
        ]
        
        # Add guest-specific info
        if session_manager.is_guest:
            role_info_controls.append(
                ft.Text(
                    "Limited to local saves only",
                    size=10,
                    color=ft.Colors.GREY_500,
                )
            )
        
        if session_manager.has_watermark():
            role_info_controls.append(
                ft.Text(
                    "⚠️ Guest videos include watermark",
                    size=10,
                    color=ft.Colors.ORANGE_400,
                )
            )
        
        role_info = ft.Column(role_info_controls, spacing=2)
        
        buttons_section = ft.Column([
            role_info,
            ft.Row([
                self.save_button,
                self.upload_button,
                self.cancel_button,
            ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # Build video list
        video_list_controls = self._build_video_list()
        
        # Calculate dynamic height for video list
        num_videos = len(self.videos)
        video_list_height = min(max(num_videos * 40, 80), 200)


        # Preview container
        preview_content = ft.Column([
            ft.Icon(ft.Icons.VIDEOCAM, size=48, color=ft.Colors.GREY_400),
            self.preview_text_label,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
        
        if self.cached_preview_path:
            preview_content = ft.Video(
                playlist=[ft.VideoMedia(self.cached_preview_path)],
                playlist_mode=ft.PlaylistMode.LOOP,
                fill_color=ft.Colors.BLACK,
                aspect_ratio=16/9,
                volume=50,
                autoplay=True,
                filter_quality=ft.FilterQuality.HIGH,
            )
        
        self.preview_container = ft.Container(
            content=preview_content,
            bgcolor=ft.Colors.with_opacity(0.05, "#000000"),
            alignment=ft.alignment.center,
            height=300,
            border_radius=8,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        # Ad banner for non-premium users
        ad_banner = None
        if session_manager.has_ads():
            ad_banner = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.AD_UNITS, color=ft.Colors.ORANGE_400),
                    ft.Text(
                        "Upgrade to Premium to remove ads and unlock unlimited features!",
                        size=12,
                        color=ft.Colors.ORANGE_400
                    ),
                    ft.TextButton(
                        "Upgrade",
                        on_click=lambda _: self._show_upgrade_message()
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.ORANGE_700),
                border=ft.border.all(1, ft.Colors.ORANGE_400),
                border_radius=5,
                padding=10,
                margin=ft.margin.only(bottom=10)
            )

        # Main layout - 2 column design: left (videos + preview), right (settings)
        main_content_items: list = [
            ft.Column([
                ft.Row([
                    # Left column: Videos list on top, Preview on bottom
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Selected Videos", size=16, weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Column(video_list_controls, scroll=ft.ScrollMode.AUTO),
                                height=video_list_height,
                                bgcolor=ft.Colors.with_opacity(0.05, "#FFFFFF"),
                                border_radius=8,
                                padding=8,
                            ),
                            ft.Container(height=10),  # Spacer
                            ft.Text("Preview", size=16, weight=ft.FontWeight.BOLD),
                            self.preview_container,
                        ], expand=True, spacing=10),
                        expand=1,
                        padding=15,
                    ),

                    # Right column: Settings and actions
                    ft.Container(
                        content=ft.Column([
                            save_settings_section,
                            ft.Divider(height=20),
                            upload_settings_section,
                            ft.Divider(height=20),
                            progress_section,
                            buttons_section,
                        ], scroll=ft.ScrollMode.AUTO, spacing=15),
                        expand=2,
                        padding=20,
                        bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
                        border_radius=10,
                    ),
                ], expand=True, spacing=15),
            ], expand=True, spacing=0)
        ]
        
        # Add ad banner for guests at top
        if should_show_ads():
            ad_banner = get_banner_ad()
            if ad_banner is not None:
                main_content_items.insert(0, ad_banner)
        
        main_content = ft.Column(main_content_items, expand=True, spacing=15)

        # Return main layout
        return ft.Container(
            content=main_content,
            padding=20,
            expand=True,
        )
    
    def _build_video_list(self):
        """Build video list display"""
        controls = []
        if not self.videos:
            controls.append(
                ft.Text("No videos selected.", color=ft.Colors.WHITE70)
            )
        else:
            for i, video_path in enumerate(self.videos):
                video_name = Path(video_path).name
                video_item = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Text(
                                str(i + 1),
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            width=30,
                            height=30,
                            bgcolor=ft.Colors.with_opacity(0.8, "#00ACC1"),
                            border_radius=15,
                            alignment=ft.alignment.center,
                        ),
                        ft.Text(
                            video_name,
                            color=ft.Colors.WHITE,
                            expand=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                    ], spacing=10),
                    padding=10,
                    bgcolor=ft.Colors.with_opacity(0.05, "#FFFFFF"),
                    border_radius=8,
                )
                controls.append(video_item)
        return controls
    
    def _browse_output_directory(self, e):
        """Open directory picker for output location"""
        def handle_directory_result(e: ft.FilePickerResultEvent):
            if e.path:
                self.output_directory = e.path
                if self.page:
                    self.page.update()
        
        dir_picker = ft.FilePicker(on_result=handle_directory_result)
        self.page.overlay.append(dir_picker)
        self.page.update()
        dir_picker.get_directory_path(dialog_title="Select output directory")
    
    def _handle_save(self, e):
        """Handle save button click - show confirmation with final settings"""
        if not self.videos:
            self._show_error("No videos to save")
            return
        
        # Show confirmation dialog with final merge settings
        self._show_save_confirmation()
    
    def _merge_final_video(self):
        """Merge videos for final save"""
        # Initialize video processor
        if not self._initialize_video_processor():
            return
        
        # Get settings
        filename = self.filename_field.value or "merged_video"
        output_path = str(Path(self.output_directory) / filename)
        codec = self.codec_dropdown.value
        video_format = self.format_dropdown.value
        
        # Show progress UI
        self._show_progress(True)
        
        # Start merging
        self.video_processor.merge_videos(
            video_paths=self.videos,
            output_path=output_path,
            codec=codec,
            video_format=video_format,
            progress_callback=self._update_progress,
            completion_callback=self._merge_complete
        )
    
    def _handle_upload(self, e):
        """Handle upload button - save and upload to YouTube"""
        if not self.videos:
            self._show_error("No videos to upload")
            return
        
        # Show upload confirmation dialog
        self._show_upload_confirmation()
    
    def _handle_cancel(self, e):
        """Cancel ongoing merge operation"""
        if self.video_processor:
            self.video_processor.cancel_processing()
            self._show_progress(False)
            self._show_info("Merge cancelled")
    
    def _show_progress(self, show: bool):
        """Toggle progress UI visibility"""
        if self.progress_bar:
            self.progress_bar.visible = show
        if self.progress_text:
            self.progress_text.visible = show
        if self.cancel_button:
            self.cancel_button.visible = show
        if self.save_button:
            self.save_button.disabled = show
        if self.upload_button:
            self.upload_button.disabled = show
        if self.page:
            self.page.update()
    
    def _update_progress(self, percentage: int, message: str):
        """Update progress bar and text"""
        if self.progress_bar and self.progress_text:
            self.progress_bar.value = percentage / 100
            self.progress_text.value = message
            if self.page:
                self.page.update()
    
    def _merge_complete(self, success: bool, message: str, output_path: str):
        """Handle merge completion"""
        self._show_progress(False)
        
        if success:
            self.merged_video_path = output_path
            if self.is_uploading:
                # Continue with upload after merge
                self._start_upload()
            else:
                self._show_success(message)
        else:
            self.is_uploading = False
            self._show_error(message)
    
    def _show_save_confirmation(self):
        """Show confirmation dialog with final merge settings"""
        filename = self.filename_field.value or "merged_video"
        codec = self.codec_dropdown.value
        video_format = self.format_dropdown.value
        output_path = str(Path(self.output_directory) / f"{filename}{video_format}")
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Save Confirmation"),
            content=ft.Column([
                ft.Text("Final merge will use:", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                ft.Row([
                    ft.Text("Filename:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(f"{filename}{video_format}", color=ft.Colors.CYAN),
                ]),
                ft.Row([
                    ft.Text("Codec:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(codec, color=ft.Colors.CYAN),
                ]),
                ft.Row([
                    ft.Text("Format:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(video_format, color=ft.Colors.CYAN),
                ]),
                ft.Row([
                    ft.Text("Location:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(output_path, color=ft.Colors.CYAN, size=10),
                ]),
                ft.Divider(height=10),
                ft.Text(
                    f"This will merge {len(self.videos)} video(s) with your specified settings.",
                    size=12,
                    color=ft.Colors.GREY_400
                ),
            ], spacing=8, tight=True),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: self._close_dialog(dialog)
                ),
                ft.TextButton(
                    "Save",
                    on_click=lambda _: self._confirm_save(dialog)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _confirm_save(self, dialog):
        """Confirm and start final merge"""
        self._close_dialog(dialog)
        self._merge_final_video()
    
    def _open_upload_settings_dialog(self, e):
        """Open dialog to edit upload settings"""
        
        # Define description presets
        presets = {
            "Professional": "Check out this merged video! Perfect for sharing with friends and family.",
            "Gaming": "Epic gaming moments compilation! Don't forget to like and subscribe for more content.",
            "Tutorial": "Step-by-step tutorial on how to merge and edit videos. Follow along and create amazing content!",
            "Vlog": "Vlog update! Hope you enjoyed this video. Let me know what you think in the comments.",
            "Music": "Original music video/compilation. Enjoy the beats!",
            "Custom": "",
        }
        
        # Create preset dropdown
        preset_dropdown = ft.Dropdown(
            label="Description Presets",
            options=[ft.dropdown.Option(key) for key in presets.keys()],
            value="Professional",
            width=200,
            on_change=lambda event: self._apply_preset(presets, event),
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Settings"),
            content=ft.Column([
                ft.Text("Video Metadata", weight=ft.FontWeight.BOLD, size=14),
                self.title_field,
                
                ft.Divider(height=10),
                ft.Text("Description", weight=ft.FontWeight.BOLD, size=12),
                ft.Column([
                    ft.Text("Quick Templates:", size=11, color=ft.Colors.GREY_500),
                    preset_dropdown,
                ], spacing=5),
                self.description_field,
                
                ft.Divider(height=10),
                self.tags_field,
                self.visibility_dropdown,
                
                ft.Divider(height=20),
                ft.Text("Privacy & Compliance", weight=ft.FontWeight.BOLD, size=14),
                self.made_for_kids_checkbox,
            ], spacing=8, tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.TextButton("Save", on_click=lambda _: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _apply_preset(self, presets: dict, event):
        """Apply a description preset"""
        selected_preset = event.control.value
        if selected_preset and selected_preset in presets:
            self.description_field.value = presets[selected_preset]
            self.page.update()
    
    def _close_dialog(self, dialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()
    
    def _show_error(self, message: str):
        """Show error snackbar"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.with_opacity(0.9, "#D32F2F"),
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _show_success(self, message: str):
        """Show success snackbar"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.with_opacity(0.9, "#00897B"),
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _show_info(self, message: str):
        """Show info snackbar"""
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.with_opacity(0.9, "#1976D2"),
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def _show_upload_success(self, video_id: str):
        """Show upload success dialog"""
        video_url = f"https://youtube.com/watch?v={video_id}"
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Successful!", color=ft.Colors.GREEN),
            content=ft.Column([
                ft.Text("Your video has been uploaded to YouTube.", size=14),
                ft.Divider(height=10),
                ft.Row([
                    ft.Text("Video ID:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(video_id, color=ft.Colors.CYAN),
                ]),
                ft.Row([
                    ft.Text("URL:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(video_url, color=ft.Colors.CYAN, size=10),
                ]),
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_upload_error(self, error_message: str):
        """Show upload error dialog"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Failed", color=ft.Colors.RED),
            content=ft.Column([
                ft.Text("An error occurred while uploading:", size=14),
                ft.Divider(height=10),
                ft.Text(
                    error_message,
                    size=12,
                    color=ft.Colors.ORANGE,
                    selectable=True
                ),
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Retry", on_click=lambda _: self._retry_upload(dialog)),
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _retry_upload(self, dialog):
        """Retry upload after error"""
        self._close_dialog(dialog)
        self.is_uploading = True
        self._upload_to_youtube()
    
    def _show_upload_confirmation(self):
        """Show confirmation dialog for upload"""
        filename = self.filename_field.value or "merged_video"
        title = self.title_field.value or filename
        description = (self.description_field.value 
                       or "Uploaded via VideoMerger App\nGitHub: https://github.com/J4ve/videomerger_app"),
        tags = self.tags_field.value or "videomerger,app"
        visibility = self.visibility_dropdown.value.lower()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload to YouTube"),
            content=ft.Column([
                ft.Text("Video will be merged and uploaded with:", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(height=10),
                ft.Row([
                    ft.Text("Title:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(title, color=ft.Colors.CYAN),
                ]),
                ft.Row([
                    ft.Text("Visibility:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(visibility.title(), color=ft.Colors.CYAN),
                ]),
                ft.Row([
                    ft.Text("Tags:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(tags, color=ft.Colors.CYAN),
                ]),
                ft.Divider(height=10),
                ft.Text(
                    "This will first merge your videos, then upload to YouTube.",
                    size=12,
                    color=ft.Colors.YELLOW
                ),

            ], spacing=8, tight=True),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda _: self._close_dialog(dialog)
                ),
                ft.TextButton(
                    "Upload",
                    on_click=lambda _: self._confirm_upload(dialog)
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _confirm_upload(self, dialog):
        """Confirm and start merge + upload process"""
        self._close_dialog(dialog)
        self.is_uploading = True
        
        # Check if video is already merged
        if self.merged_video_path and Path(self.merged_video_path).exists():
            self._start_upload()
        else:
            # Need to merge first
            self._merge_final_video()
    
    def _start_upload(self):
        """Start YouTube upload process"""
        self._update_progress(10, "Preparing upload...")
        self._show_progress(True)
        
        # Upload video directly
        self._upload_to_youtube()
    
    def _upload_to_youtube(self):
        """Upload merged video to YouTube using uploader module"""
        if not self.merged_video_path:
            self._show_error("Video file not available")
            return
        
        try:
            from uploader.uploader import YouTubeUploader, UploadSettings
            from uploader.metadata import build_metadata_from_form
            
            # Create uploader instance
            uploader = YouTubeUploader()
            
            # Check if user is already authenticated through session
            if not session_manager.is_logged_in:
                self._show_error("Please login first")
                return
                
            # Authenticate with YouTube - this will use browser OAuth
            self._update_progress(20, "Authenticating with YouTube...")
            authenticated = uploader.authenticate()
            
            if not authenticated:
                self._show_error("YouTube authentication failed")
                return
            
            # Get upload settings from form
            metadata = build_metadata_from_form(
                title=self.title_field.value or "Merged Video",
                description=(self.description_field.value 
                       or "Uploaded via VideoMerger App\nGitHub: https://github.com/J4ve/videomerger_app"),
                tags=self.tags_field.value or "",
                visibility=self.visibility_dropdown.value.lower(),
                made_for_kids=self.made_for_kids_checkbox.value
            )

            settings = UploadSettings(
                title=metadata.title,
                description=metadata.description,
                tags=metadata.tags,
                visibility=metadata.visibility,
                made_for_kids=metadata.made_for_kids
            )
            
            self._update_progress(40, "Uploading to YouTube...")
            
            # Upload video with progress callback
            result = uploader.upload_video(
                video_path=self.merged_video_path,
                settings=settings,
                progress_callback=lambda p, m: self._update_progress(int(40 + p * 0.6), m)
            )
            
            self._update_progress(100, "Upload complete!")
            self._show_progress(False)
            self.is_uploading = False
            
            # Show success dialog
            video_id = result.get('video_id')
            self._show_upload_success(video_id)
            
        except Exception as e:
            self.is_uploading = False
            self._show_progress(False)
            self._show_upload_error(str(e))
    
    def _show_upload_success(self, video_id: str):
        """Show upload success dialog"""
        video_url = f"https://youtube.com/watch?v={video_id}"
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Successful!", color=ft.Colors.GREEN),
            content=ft.Column([
                ft.Text("Your video has been uploaded to YouTube.", size=14),
                ft.Divider(height=10),
                ft.Row([
                    ft.Text("Video ID:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(video_id, color=ft.Colors.CYAN),
                ]),
                ft.Row([
                    ft.Text("URL:", weight=ft.FontWeight.BOLD, width=100),
                    ft.Text(video_url, color=ft.Colors.CYAN, size=10),
                ]),
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("OK", on_click=lambda _: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_upload_error(self, error_message: str):
        """Show upload error dialog"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Failed", color=ft.Colors.RED),
            content=ft.Column([
                ft.Text("An error occurred while uploading:", size=14),
                ft.Divider(height=10),
                ft.Text(
                    error_message,
                    size=12,
                    color=ft.Colors.ORANGE,
                    selectable=True
                ),
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Retry", on_click=lambda _: self._retry_upload(dialog)),
                ft.TextButton("Close", on_click=lambda _: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _retry_upload(self, dialog):
        """Retry upload after error"""
        self._close_dialog(dialog)
        self.is_uploading = True
        self._upload_to_youtube()

    def _show_upgrade_message(self):
        """Show upgrade message using snack bar"""
        if self.page:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Upgrade feature coming soon!"))
            self.page.snack_bar.open = True
            self.page.update()