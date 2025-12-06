"""
Main Window - Wizard Navigation
"""

import flet as ft
from configs.config import Config
from .login_screen import LoginScreen
from .selection_screen import SelectionScreen
from .arrangement_screen import ArrangementScreen
from .save_upload_screen import SaveUploadScreen
from .config_tab import ConfigTab
from .admin_dashboard import AdminDashboardScreen
from access_control.session import session_manager
from access_control.roles import Permission
import sys
import platform
from datetime import datetime


class MainWindow:
    """Main application window with stepper navigation"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_step = 0  # 0=Select, 1=Arrange, 2=Save/Upload
        self.selected_videos = []  # Shared state across screens, (IMPORTANT)
        self.next_button = None  # Next button at bottom right
        self.selection_screen = SelectionScreen(page=self.page) #selection screen
        self.arrangement_screen = ArrangementScreen(page=self.page) #arrangement screen
        self.save_upload_screen = SaveUploadScreen(page=self.page) #save/upload screen
        
        # Admin dashboard (only initialized if user has permission)
        self.admin_dashboard = None
        self.current_view = "wizard"  # "wizard" or "admin"

        # User info components
        self.user_info_text = None
        self.logout_button = None

        # stepper indicator thingies
        # Step 1: Select Videos
        self.step1_indicator = ft.Column([
            ft.Container(
                content=ft.Text("1", color=ft.Colors.WHITE),  # Number in circle
                width=40,
                height=40,
                bgcolor=ft.Colors.with_opacity(0.9, "#00897B"),  # Green-blue active color
                border_radius=20,  # Half of width/height = circle!
                alignment=ft.alignment.center,
            ),
            ft.Text("Select Videos", size=12),  # Label below
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5,
        )
        
        self.first_line_step_indicator = ft.Container(  # Line
            height=2,  # Thin line
            bgcolor=ft.Colors.with_opacity(0.5, "#37474F"),  # Dark line color
            expand=True,  # Stretch
            margin=ft.margin.only(bottom=22), # 22 lol perfect pantay na haha
        )
        
        # Step 2: Arrange and Merge
        self.step2_indicator = ft.Column([
            ft.Container(
                content=ft.Text("2", color=ft.Colors.WHITE),  # Number in circle
                width=40,
                height=40,
                bgcolor=ft.Colors.with_opacity(0.7, "#37474F"),  # Dark inactive color
                border_radius=20,
                alignment=ft.alignment.center,
            ),
            ft.Text("Arrange and Merge", size=12),  # Label below
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5,
        )
        
        self.second_line_step_indicator = ft.Container(  # Line
            height=2,
            bgcolor=ft.Colors.with_opacity(0.5, "#37474F"),  # Dark line color
            expand=True,  # Stretch
            margin=ft.margin.only(bottom=22), # 22 lol perfect pantay na haha
        )
        
        # Step 3: Save/Upload
        self.step3_indicator = ft.Column([
            ft.Container(
                content=ft.Text("3", color=ft.Colors.WHITE),  # Number in circle
                width=40,
                height=40,
                bgcolor=ft.Colors.with_opacity(0.7, "#37474F"),  # Dark inactive color
                border_radius=20,
                alignment=ft.alignment.center,
            ),
            ft.Text("Save/Upload", size=12),  # Label below
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5,
        )

        self.setup_page()
        
    def setup_page(self):
        """Configure page settings"""
        self.page.title = Config.APP_TITLE
        self.page.window.width = Config.APP_WIDTH
        self.page.window.height = Config.APP_HEIGHT
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = ft.Colors.with_opacity(0.95, "#272822")  # Monokai-like dark background
        self.page.padding = 0
        
    def go_to_step(self, step):
        """Navigate to specific step"""
        self.current_step = step
        
        # Update stepper colors based on current step

        #circles
        self.step1_indicator.controls[0].bgcolor = ft.Colors.with_opacity(0.9, "#00897B") if step >= 0 else ft.Colors.with_opacity(0.7, "#37474F")
        self.step2_indicator.controls[0].bgcolor = ft.Colors.with_opacity(0.9, "#00897B") if step >= 1 else ft.Colors.with_opacity(0.7, "#37474F")
        self.step3_indicator.controls[0].bgcolor = ft.Colors.with_opacity(0.9, "#00897B") if step >= 2 else ft.Colors.with_opacity(0.7, "#37474F")

        #lines
        self.first_line_step_indicator.bgcolor = ft.Colors.with_opacity(0.9, "#00897B") if step >= 1 else ft.Colors.with_opacity(0.5, "#37474F")
        self.second_line_step_indicator.bgcolor = ft.Colors.with_opacity(0.9, "#00897B") if step >= 2 else ft.Colors.with_opacity(0.5, "#37474F")

        
        self.page.controls = [self.build()]
        self.page.update()

        
    def next_step(self):
        """Move to next wizard step"""
        if self.current_step < 2:
            self.current_step += 1
            
            # Pass selected videos and page reference to arrangement screen when moving to step 1
            if self.current_step == 1:
                self.arrangement_screen.set_videos(self.selection_screen.selected_files)
                self.arrangement_screen.main_window = self  # Pass reference to main window

            elif self.current_step == 2:
                self.save_upload_screen.set_videos(self.arrangement_screen.videos)
                self.save_upload_screen.main_window = self
            
            self.go_to_step(self.current_step)
        
    def previous_step(self):
        """Move to previous wizard step"""
        if self.current_step > 0:
            self.current_step -= 1
            self.go_to_step(self.current_step)
    
    def next_button_clicked(self, e):
        """Handle next button click - delegate to current screen"""
        print("next button clicked")
        # Call the current screen's validation/next handler
        if not self.selection_screen.selected_files:
            print("Error: no files")
            # Show error for empty selected files
            snackbar_no_files = ft.SnackBar(
                content=ft.Text("Please select at least one video file", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.with_opacity(0.9, "#f03a1a"),
            )
            self.page.overlay.append(snackbar_no_files)
            snackbar_no_files.open = True
            self.page.update()
        else:
            print("files found: calling next_step()")
            if self.current_step == 0:
                # SelectionScreen will handle validation
                self.next_step()
            elif self.current_step == 1:
                # ArrangementScreen validation
                self.next_step()
            elif self.current_step == 2:
                # SaveUploadScreen validation
                pass

    def back_button_clicked(self, e):
        """Handle back button click - delegate to current screen"""
        print("back button clicked")
        if self.current_step > 0:
            self.previous_step()
        
    def build(self):
        """Build and return the main layout"""
        # Display current screen based on self.current_step
        match self.current_step:
            case 0:
                content = self.selection_screen.build()
            case 1:
                content = self.arrangement_screen.build()
            case 2:
                content = self.save_upload_screen.build()

        # User info section at top right
        user_info = session_manager.get_user_display_info()
        # Show user's name if available, otherwise fall back to email
        display_name = user_info.get('name') or user_info.get('email', 'User')
        
        # Profile button with user photo and name - only show profile image for authenticated users
        user_picture_url = user_info.get('picture', '')
        is_guest = session_manager.is_guest
        
        if user_picture_url and not is_guest:
            # Authenticated user with profile picture - show image only
            profile_image = ft.CircleAvatar(
                foreground_image_src=user_picture_url,
                radius=16,
                bgcolor=ft.Colors.BLUE_700
            )
        else:
            # Guest user or no picture - use icon only for guests
            profile_image = ft.CircleAvatar(
                content=ft.Icon(ft.Icons.PERSON, size=20, color=ft.Colors.WHITE),
                radius=16,
                bgcolor=ft.Colors.GREY_700
            )
        
        self.profile_button = ft.Container(
            content=ft.Row([
                profile_image,
                ft.Text(display_name, size=13, weight=ft.FontWeight.W_500)
            ], spacing=8, tight=True),
            on_click=self._open_settings,
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.1, "#00ACC1"),
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, "#00ACC1")),
            tooltip="Settings & Account",
            ink=True,
            animate=ft.Animation(100, "easeOut")
        )
        
        # Admin dashboard button removed from main window (now in config tab)
        
        user_section = ft.Container(
            content=self.profile_button,
            right=20,
            top=20
        )

        # Settings dialog will be shown when settings button is clicked

        # build the stepper indicator (responsive with side padding)
        stepper = ft.Container(
            content=ft.Row([
                self.step1_indicator,
                self.first_line_step_indicator,
                self.step2_indicator,
                self.second_line_step_indicator,
                self.step3_indicator,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=15,
            margin=ft.margin.symmetric(horizontal=170, vertical=10),
            expand=False,
        )

        # Fixed next button at bottom right
        self.next_button = ft.Container(
            content=ft.ElevatedButton(
                text="Next",
                style=ft.ButtonStyle(
                    text_style=ft.TextStyle(size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
                    shape=ft.RoundedRectangleBorder(radius=12),
                    elevation=2,
                    shadow_color=ft.Colors.with_opacity(0.2, "#000000"),
                    padding=ft.padding.symmetric(horizontal=20, vertical=15),
                ),
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.with_opacity(0.85, "#00897B"),  # Brighter green-blue for buttons
                icon=ft.Icons.ARROW_FORWARD,
                icon_color=ft.Colors.WHITE,
                on_click=self.next_button_clicked,
                height=55,
                width=160,
                animate_scale=ft.Animation(200, "easeOutCubic"),
            ),
            right=30,
            bottom=40,
            visible=(self.current_step != 2) # pag nasa last step, next button will disappear
        )

        # Back button at top left, small, icon only
        self.back_button = ft.Container(
            content=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                icon_color=ft.Colors.with_opacity(0.8, "#00ACC1"),
                on_click=self.back_button_clicked,
                width=40,
                height=40,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    bgcolor=ft.Colors.with_opacity(0.1, "#00ACC1"),
                    overlay_color=ft.Colors.with_opacity(0.2, "#00ACC1"),
                ),
                animate_scale=ft.Animation(200, "easeOutCubic"),
            ),
            left=20,
            top=20,
        )

        # Check if we should show admin dashboard or wizard
        if self.current_view == "admin":
            # Show admin dashboard instead of wizard
            if self.admin_dashboard is None:
                self.admin_dashboard = AdminDashboardScreen(self.page)
            # Always reload users when switching to admin view
            self.admin_dashboard.load_users()
            admin_content = self.admin_dashboard.build()
            stack_children = [
                admin_content,
                user_section,
            ]
            return ft.Stack(
                stack_children,
                expand=True,
            )
        else:
            # Show normal wizard view
            stack_children = [
                ft.Column(
                    [
                        stepper,
                        ft.Divider(),
                        content,
                    ],
                    expand=True,
                ),
                self.next_button,  # Fixed position overlay
                user_section,  # User info at top right
            ]
            if self.current_step > 0:
                stack_children.append(self.back_button)  # Show back button only if not at first step
            return ft.Stack(
                stack_children,
                expand=True,
            )
    
    def _handle_logout(self, e):
        print("logout clicked")
        try:
            session_manager.logout(clear_tokens=False)
        except Exception as ex:
            print(f"logout error: {ex}")
        try:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Signing out..."))
            self.page.snack_bar.open = True
            self.page.update()
        except Exception:
            pass
        self._return_to_login()
    
    def _return_to_login(self):
        """Return to login screen after logout"""
        print("Returning to login screen...")
        try:
            # Clear all overlays and dialogs
            self.page.dialog = None
            self.page.overlay.clear()
            self.page.clean()
        except Exception as ex:
            print(f"Error clearing page: {ex}")
        
        # Small delay to ensure page is clean
        import time
        time.sleep(0.1)
        
        # Show login screen
        def handle_login_complete(user_info, role):
            print(f"Re-login complete: {user_info}, Role: {role.name}")
            session_manager.login(user_info, role)
            self.page.clean()
            self.page.update()
            try:
                new_window = MainWindow(self.page)
                main_layout = new_window.build()
                self.page.controls = [main_layout]
                self.page.update()
                
                # Show welcome message
                snack_bar = ft.SnackBar(
                    content=ft.Text(f"Welcome, {user_info.get('name') or user_info.get('email', 'Guest')}!")
                )
                self.page.overlay.append(snack_bar)
                snack_bar.open = True
                self.page.update()
            except Exception as ex:
                print(f"Error recreating main window: {ex}")
                self.page.add(ft.Text(f"Error: {str(ex)}", color=ft.Colors.RED))
                self.page.update()
        
        try:
            login_screen = LoginScreen(self.page, on_login_complete=handle_login_complete)
            login_ui = login_screen.build()
            self.page.controls = [login_ui]
            self.page.update()
        except Exception as ex:
            print(f"Error showing login screen: {ex}")
    
    def _open_settings(self, e):
        """Open settings dialog"""
        from access_control.roles import RoleType
        
        def close_settings(e):
            dialog.open = False
            self.page.update()
        
        def logout_and_close(e):
            dialog.open = False
            self.page.update()
            self._handle_logout(e)
        
        def on_login_click(e):
            """Handle login suggestion click from guest config"""
            try:
                dialog.open = False
                self.page.update()
            except Exception as ex:
                print(f"Error closing dialog: {ex}")
            self._return_to_login()
        
        # Create config tab instance with callbacks
        config_tab = ConfigTab(self.page, on_logout_clicked=logout_and_close, on_login_clicked=on_login_click)
        config_content = config_tab.build()
        
        # Determine if user is guest to customize dialog actions
        is_guest = session_manager.is_guest
        
        # Build actions list based on user type
        actions = []
        if is_guest:
            actions.append(
                ft.TextButton(
                    "Back to Login",
                    icon=ft.Icons.LOGIN,
                    on_click=on_login_click,
                    style=ft.ButtonStyle(color=ft.Colors.BLUE_400)
                )
            )
        else:
            actions.append(
                ft.TextButton(
                    "Logout",
                    icon=ft.Icons.LOGOUT,
                    on_click=logout_and_close,
                    style=ft.ButtonStyle(color=ft.Colors.RED_400)
                )
            )
        
        actions.append(ft.TextButton("Close", on_click=close_settings))
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.BLUE_400),
                ft.Text("User Settings & Configuration", size=18)
            ], spacing=10),
            content=ft.Container(
                content=config_content,
                width=900,
                height=650,
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _toggle_admin_dashboard(self, e):
        """Toggle between wizard and admin dashboard views"""
        if self.current_view == "wizard":
            self.current_view = "admin"
        else:
            self.current_view = "wizard"
        
        # Rebuild the page
        self.page.controls = [self.build()]
        self.page.update()
