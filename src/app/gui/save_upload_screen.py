
import flet as ft
from configs.config import Config
from datetime import datetime
from pathlib import Path


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
        
        # Progress tracking
        self.progress_bar = None
        self.progress_text = None
        self.save_button = None
        self.upload_button = None
        self.cancel_button = None
        
        # Output path
        self.output_directory = str(Path.home() / "Videos" / "VideoMerger")
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)

    def set_videos(self, videos):
        self.videos = videos or []
        
    def _initialize_video_processor(self):
        """Lazy load video processor"""
        if self.video_processor is None:
            from app.video_processor import VideoProcessor
            self.video_processor = VideoProcessor()
            
            # Check FFmpeg availability
            if not self.video_processor.check_ffmpeg():
                self._show_error("FFmpeg not found. Please install FFmpeg to merge videos.")
        
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
        
        upload_settings_section = ft.Column([
            ft.Text("Upload Settings", size=16, weight=ft.FontWeight.BOLD),
            ft.Text("Configure metadata for YouTube upload", size=12, color=ft.Colors.GREY_400),
            ft.ElevatedButton(
                "Edit Upload Settings",
                icon=ft.Icons.EDIT,
                on_click=self._open_upload_settings_dialog
            ),
        ], spacing=10)

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

        # Buttons section
        self.save_button = ft.ElevatedButton(
            "Save Video",
            icon=ft.Icons.SAVE,
            bgcolor=ft.Colors.with_opacity(0.85, "#00897B"),
            color=ft.Colors.WHITE,
            on_click=self._handle_save,
            height=45,
            width=150
        )
        
        self.upload_button = ft.ElevatedButton(
            "Save & Upload",
            icon=ft.Icons.UPLOAD,
            bgcolor=ft.Colors.with_opacity(0.85, "#1976D2"),
            color=ft.Colors.WHITE,
            on_click=self._handle_upload,
            height=45,
            width=150,
            disabled=True  # TODO: Enable when YouTube API is implemented
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
        
        buttons_section = ft.Row([
            self.save_button,
            self.upload_button,
            self.cancel_button,
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        # Build video list
        video_list_controls = self._build_video_list()
        
        # Calculate dynamic height for video list
        num_videos = len(self.videos)
        video_list_height = min(max(num_videos * 40, 80), 200)

        # Main layout
        return ft.Container(
            content=ft.Row([
                # Left column: Video list and preview
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
                        ft.Container(height=10),
                        ft.Text("Preview", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.VIDEOCAM,
                                size=48,
                                color=ft.Colors.GREY_400
                            ),
                            bgcolor=ft.Colors.with_opacity(0.05, "#000000"),
                            alignment=ft.alignment.center,
                            height=250,
                            border_radius=8,
                        ),
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
                self.page.update()
        
        dir_picker = ft.FilePicker(on_result=handle_directory_result)
        self.page.overlay.append(dir_picker)
        self.page.update()
        dir_picker.get_directory_path(dialog_title="Select output directory")
    
    def _handle_save(self, e):
        """Handle save button click - merge videos"""
        if not self.videos:
            self._show_error("No videos to merge")
            return
        
        # Initialize video processor
        self._initialize_video_processor()
        if not self.video_processor:
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
        # TODO: Implement YouTube upload after video merge
        self._show_error("YouTube upload not yet implemented")
    
    def _handle_cancel(self, e):
        """Cancel ongoing merge operation"""
        if self.video_processor:
            self.video_processor.cancel_processing()
            self._show_progress(False)
            self._show_info("Merge cancelled")
    
    def _show_progress(self, show: bool):
        """Toggle progress UI visibility"""
        self.progress_bar.visible = show
        self.progress_text.visible = show
        self.cancel_button.visible = show
        self.save_button.disabled = show
        self.upload_button.disabled = True  # Keep disabled for now
        if self.page:
            self.page.update()
    
    def _update_progress(self, percentage: int, message: str):
        """Update progress bar and text"""
        if self.progress_bar and self.progress_text:
            self.progress_bar.value = percentage / 100
            self.progress_text.value = message
            if self.page:
                self.page.update()
    
    def _merge_complete(self, success: bool, message: str):
        """Handle merge completion"""
        self._show_progress(False)
        
        if success:
            self._show_success(message)
        else:
            self._show_error(message)
    
    def _open_upload_settings_dialog(self, e):
        """Open dialog to edit upload settings"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Upload Settings"),
            content=ft.Column([
                self.title_field,
                self.description_field,
                self.tags_field,
                self.visibility_dropdown,
            ], spacing=10, tight=True),
            actions=[
                ft.TextButton("Save", on_click=lambda _: self._close_dialog(dialog)),
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
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