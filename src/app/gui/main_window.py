"""
Main Window - Wizard Navigation
"""

import flet as ft
from configs.config import Config
from .selection_screen import SelectionScreen
from .arrangement_screen import ArrangementScreen
from .save_upload_screen import SaveUploadScreen
from .config_tab import ConfigTab
from access_control.session import session_manager


class MainWindow:
    """Main application window with stepper navigation"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_step = 0  # 0=Select, 1=Arrange, 2=Save/Upload
        self.selected_videos = []  # Shared state across screens, (IMPORTANT)
        self.next_button = None  # Next button at bottom right
        self.selection_screen = SelectionScreen(page=self.page) #selection screen
        print(f"SelectionScreen created: {self.selection_screen}")
        self.arrangement_screen = ArrangementScreen(page=self.page) #arrangement screen
        self.save_upload_screen = SaveUploadScreen(page=self.page) #save/upload screen

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
        self.page.window_width = Config.APP_WIDTH
        self.page.window_height = Config.APP_HEIGHT
        self.page.window.center() 
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = ft.Colors.with_opacity(0.95, "#272822")  # Monokai-like dark background
        self.page.padding = 0
        # TODO: Add app bar with config button
        
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
        self.user_info_text = ft.Text(
            f"{display_name} ({user_info['role']})",
            size=12,
            color=ft.Colors.CYAN_400
        )
        
        self.logout_button = ft.IconButton(
            icon=ft.Icons.LOGOUT,
            icon_color=ft.Colors.RED_400,
            tooltip="Logout",
            on_click=self._handle_logout,
            width=30,
            height=30
        )
        
        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_color=ft.Colors.GREY_400,
            tooltip="Settings & Templates",
            on_click=self._open_settings,
            width=30,
            height=30
        )
        
        user_section = ft.Container(
            content=ft.Row([
                self.user_info_text,
                self.settings_button,
                self.logout_button
            ], spacing=5, alignment=ft.MainAxisAlignment.END),
            right=20,
            top=20
        )

        # Settings dialog will be shown when settings button is clicked

        # build the stepper indicator
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
            padding=ft.padding.only(top=20, left=200, right=200),
            bgcolor=ft.Colors.with_opacity(0.1, "#1A1A1A"),
            border_radius=15,
            margin=ft.margin.symmetric(horizontal=20, vertical=10),
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
        """Handle logout button click"""
        # Show confirmation dialog
        def confirm_logout(e):
            dialog.open = False
            self.page.update()
            
            session_manager.logout()
            
            # Restart the app by clearing page and showing login screen again
            self.page.clean()
            from access_control.gui.auth_screen import LoginScreen
            
            def handle_login_complete(user_info, role):
                session_manager.login(user_info, role)
                self.page.clean()
                new_window = MainWindow(self.page)
                self.page.add(new_window.build())
                self.page.update()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Welcome back, {user_info.get('name') or user_info.get('email', 'Guest')}!"),
                    action="OK"
                )
                self.page.snack_bar.open = True
                self.page.update()
            
            login_screen = LoginScreen(self.page, on_login_complete=handle_login_complete)
            self.page.add(login_screen.build())
            self.page.update()
        
        def cancel_logout(e):
            dialog.open = False
            self.page.update()
        
        # Get user display name safely
        user_name = None
        if session_manager.current_user:
            user_name = session_manager.current_user.get('name')
        user_display = user_name or session_manager.email or 'User'
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Logout"),
            content=ft.Text(f"Are you sure you want to logout {user_display}?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_logout),
                ft.TextButton("Logout", on_click=confirm_logout),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _open_settings(self, e):
        """Open settings dialog"""
        def close_settings(e):
            dialog.open = False
            self.page.update()
        
        # Create config tab instance
        config_tab = ConfigTab(self.page)
        config_content = config_tab.build()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.BLUE_400),
                ft.Text("Settings & Configuration", size=18)
            ], spacing=10),
            content=ft.Container(
                content=config_content,
                width=800,
                height=600,
            ),
            actions=[
                ft.TextButton("Close", on_click=close_settings),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
