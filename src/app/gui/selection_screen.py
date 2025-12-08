"""
Selection Screen - Video selection (Step 1)
"""

import flet as ft
from configs.config import Config
from pathlib import Path
from app.video_core.video_metadata import VideoMetadata
from app.services.ad_manager import ad_manager


class SelectionScreen:
    """First screen: File selection with FilePicker"""
    
    def __init__(self, page: ft.Page, parent_window=None):
        self.page = page
        self.parent_window = parent_window
        self.selected_files = []  # Store selected video files
        self.original_order = []  # Store original order to detect arrangement changes
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
                        
                        # Get metadata
                        metadata = VideoMetadata(file_path)
                        metadata_text = metadata.get_short_info()
                        
                        # Add to visual list
                        self.file_list.controls.append(
                            ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.VIDEO_FILE, size=16),
                                    ft.Column([
                                        ft.Text(file.name, size=12, weight=ft.FontWeight.BOLD),
                                        ft.Text(metadata_text, size=10, color=ft.Colors.GREY_400),
                                    ], spacing=2, expand=True),
                                    ft.IconButton(
                                        icon=ft.Icons.CLOSE,
                                        icon_size=16,
                                        on_click=lambda _, path=file_path: self.remove_file(path)
                                    ),
                                ]),
                            ], spacing=5)
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
            
            self.page.update()
    
    def remove_file(self, file_path):
        """Remove file from selection"""
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            # Rebuild file list display with metadata
            self.file_list.controls = []
            for f in self.selected_files:
                metadata = VideoMetadata(f)
                metadata_text = metadata.get_short_info()
                
                self.file_list.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.VIDEO_FILE, size=16),
                            ft.Column([
                                ft.Text(Path(f).name, size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(metadata_text, size=10, color=ft.Colors.GREY_400),
                            ], spacing=2, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                on_click=lambda _, path=f: self.remove_file(path)
                            ),
                        ]),
                    ], spacing=5)
                )
            
            # Toggle visibility when no files left
            if self.files_display and self.select_zone_container:
                has_files = len(self.selected_files) > 0
                self.files_display.visible = has_files
                self.select_zone_container.visible = not has_files
            
            self.page.update()
    
    def _show_premium_coming_soon(self):
        """Show premium purchase dialog"""
        from access_control.session import session_manager
        
        # Check if guest user
        if session_manager.is_guest:
            self._show_guest_login_prompt()
            return
        
        # Check if not logged in
        if not session_manager.is_logged_in:
            self._show_login_prompt()
            return
        
        # Show purchase dialog
        self._show_premium_purchase_dialog()
    
    def _show_guest_login_prompt(self):
        """Prompt guest to login before purchasing"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.LOGIN, color=ft.Colors.BLUE_400),
                ft.Text("Login Required", color=ft.Colors.BLUE_400),
            ]),
            content=ft.Column([
                ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=64, color=ft.Colors.BLUE_400),
                ft.Text(
                    "Please login to purchase premium",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Your purchase will be saved to your account so you can access premium features on any device.",
                    size=12,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.GREY_400,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Login",
                    icon=ft.Icons.LOGIN,
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: self._redirect_to_login(dialog),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _show_login_prompt(self):
        """Prompt user to login"""
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Login Required"),
            content=ft.Text("Please login to purchase premium features."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
                ft.ElevatedButton("Login", on_click=lambda _: self._redirect_to_login(dialog)),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _redirect_to_login(self, dialog):
        """Close dialog and trigger login flow"""
        self._close_dialog(dialog)
        
        # Trigger return to login screen for OAuth authentication
        if hasattr(self, 'parent_window') and self.parent_window:
            try:
                self.parent_window._return_to_login()
            except Exception as e:
                print(f"Error triggering login: {e}")
                # Fallback to showing snackbar
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text("Please use the Login button in the top right to sign in."),
                        bgcolor=ft.Colors.BLUE_700
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
        else:
            # Show snackbar prompting to use login button
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Please click the Login button in the top right to sign in."),
                    bgcolor=ft.Colors.BLUE_700
                )
                self.page.snack_bar.open = True
                self.page.update()
    
    def _close_dialog(self, dialog):
        """Close dialog helper"""
        dialog.open = False
        self.page.update()
    
    def _show_premium_purchase_dialog(self):
        """Show premium purchase dialog with plan options"""
        from access_control.purchase_service import PurchaseService, PurchasePlan
        from access_control.session import session_manager
        
        # Check if guest user
        if session_manager.is_guest:
            self._show_guest_login_prompt()
            return
        
        # Check if not logged in
        if not session_manager.is_logged_in:
            self._show_login_prompt()
            return
        
        # Get plan information
        plans = PurchaseService.get_all_plans()
        
        def handle_purchase(plan_name: str):
            """Handle premium purchase"""
            dialog.open = False
            self.page.update()
            
            # Show processing message
            processing_snack = ft.SnackBar(
                content=ft.Text("➡️ Redirecting to payment gateway..."),
                bgcolor=ft.Colors.BLUE_700
            )
            self.page.snack_bar = processing_snack
            self.page.snack_bar.open = True
            self.page.update()
            
            # Process purchase
            result = session_manager.purchase_premium(plan_name)
            
            # Show result
            if result.get('status') and hasattr(result['status'], 'value'):
                status_value = result['status'].value
            else:
                status_value = result.get('status')
            
            if status_value == 'success':
                success_snack = ft.SnackBar(
                    content=ft.Text(f"✓ Welcome to Premium! {result.get('message', '')}"),
                    bgcolor=ft.Colors.GREEN_700
                )
                self.page.snack_bar = success_snack
                self.page.snack_bar.open = True
                self.page.update()
                
                # Refresh UI to reflect premium status
                if hasattr(self, 'content') and self.content:
                    self.content = self.build()
                    self.page.update()
            else:
                error_snack = ft.SnackBar(
                    content=ft.Text(f"Purchase failed: {result.get('message', 'Unknown error')}"),
                    bgcolor=ft.Colors.RED_700
                )
                self.page.snack_bar = error_snack
                self.page.snack_bar.open = True
                self.page.update()
        
        # Create plan card (single lifetime plan)
        plan = plans[0]  # Only one plan now
        
        card = ft.Container(
            content=ft.Column([
                # Plan header
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "LIFETIME PREMIUM",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.AMBER_400,
                        ),
                        ft.Text(
                            plan['description'],
                            size=12,
                            color=ft.Colors.GREY_400,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    padding=10,
                ),
                
                # Payment Gateway Info
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PAYMENT, size=40, color=ft.Colors.AMBER_400),
                        ft.Text(
                            "Secure Payment",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.AMBER_400,
                        ),
                        ft.Text(
                            "You'll be redirected to our payment gateway",
                            size=11,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            "PayMongo / GCash / PayPal",
                            size=10,
                            italic=True,
                            color=ft.Colors.GREY_600,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    padding=ft.padding.symmetric(vertical=15),
                ),
                
                # Purchase button
                ft.ElevatedButton(
                    "Continue to Payment",
                    icon=ft.Icons.ARROW_FORWARD,
                    bgcolor=ft.Colors.AMBER_700,
                    color=ft.Colors.WHITE,
                    on_click=lambda _: handle_purchase(plan['plan']),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
            border=ft.border.all(2, ft.Colors.AMBER_400),
            border_radius=10,
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.AMBER_400),
        )
        
        # Create dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.STAR, color=ft.Colors.AMBER_400),
                ft.Text("Upgrade to Premium", color=ft.Colors.AMBER_400),
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Unlock all premium features:",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    
                    # Features list
                    ft.Container(
                        content=ft.Column([
                            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN_400), 
                                   ft.Text("Unlimited video arrangements", size=12)], spacing=5),
                            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN_400), 
                                   ft.Text("No advertisements", size=12)], spacing=5),
                            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN_400), 
                                   ft.Text("Direct YouTube upload", size=12)], spacing=5),
                            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN_400), 
                                   ft.Text("Priority support", size=12)], spacing=5),
                        ], spacing=8),
                        padding=10,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREEN_400),
                        border_radius=5,
                    ),
                    
                    ft.Container(height=10),
                    
                    # Plan card
                    card,
                    
                    ft.Container(height=5),
                    
                    ft.Text(
                        "🔒 Secure payment processing via PayMongo/GCash/PayPal",
                        size=10,
                        italic=True,
                        color=ft.Colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, scroll=ft.ScrollMode.AUTO),
                width=400,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
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
        # Fixed height for 5 videos (5 * 30px = 150px), scrollable if more
        self.file_list_container = ft.Container(
            content=ft.Column(
                [self.file_list],
                scroll=ft.ScrollMode.AUTO,
            ),
            width=700,
            height=150,
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
        
        # Unlock Premium button (coming soon) - only show if user doesn't have premium access
        from access_control.session import session_manager
        has_premium_access = session_manager.is_premium() or session_manager.is_admin()
        unlock_premium_button = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.STAR, size=16, color=ft.Colors.AMBER_400),
                ft.Text("Unlock Premium", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
            ], spacing=5, tight=True),
            padding=ft.padding.symmetric(horizontal=6, vertical=6),
            bgcolor=ft.Colors.with_opacity(0.15, "#FFA500"),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.AMBER_700),
            on_click=lambda _: self._show_premium_coming_soon(),
            tooltip="Upgrade to Premium",
            visible=not has_premium_access,
            alignment=ft.alignment.center,
        )
        
        # Create vertical side ad
        horizontal_ad = ad_manager.create_vertical_side_ad(self.page, width=300, height=250)

        # Main content area
        main_content = ft.Column(
            [
                # Header
                ft.Text("Select Videos", size=24, weight=ft.FontWeight.BOLD, color=accent),
                ft.Text(f"Supported formats: .mp4, .mkv, .mov, .avi, and more…", size=12, color=dark_text),

                ft.Container(height=20),  # Spacer

                # Selection zone (hidden when files are selected)
                self.select_zone_container,

                # Selected files (replaces drop zone when files exist)
                self.files_display,
                
                # Unlock Premium button below - only show if user doesn't have premium access
                ft.Row([unlock_premium_button], alignment=ft.MainAxisAlignment.CENTER) if not has_premium_access else ft.Container(),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

        return ft.Container(
            content=ft.Row(
                [
                    main_content,
                    horizontal_ad,
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            padding=40,
            expand=True,
            bgcolor=monokai_bg,
        )