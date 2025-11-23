"""
Main Window - Wizard Navigation
"""

import flet as ft
from configs.config import Config
from .selection_screen import SelectionScreen
from .arrangement_screen import ArrangementScreen
from .save_upload_screen import SaveUploadScreen
from .config_tab import ConfigTab


class MainWindow:
    """Main application window with stepper navigation"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_step = 0  # 0=Select, 1=Arrange, 2=Save/Upload
        self.selected_videos = []  # Shared state across screens
        self.next_button = None  # Next button at bottom right
        self.setup_page()
        
    def setup_page(self):
        """Configure page settings"""
        self.page.title = Config.APP_TITLE
        self.page.window_width = Config.APP_WIDTH
        self.page.window_height = Config.APP_HEIGHT
        self.page.window.center() 
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        # TODO: Add app bar with config button
        
    def go_to_step(self, step):
        """Navigate to specific step"""
        # TODO: Validate step transition
        # TODO: Update current_step
        # TODO: Rebuild UI with new screen
        pass
        
    def next_step(self):
        """Move to next wizard step"""
        # TODO: Validate current step data
        # TODO: Call go_to_step(current_step + 1)
        pass
        
    def previous_step(self):
        """Move to previous wizard step"""
        # TODO: Call go_to_step(current_step - 1)
        pass
    
    def next_button_clicked(self, e):
        """Handle next button click - delegate to current screen"""
        # Call the current screen's validation/next handler
        if self.current_step == 0:
            # SelectionScreen will handle validation
            pass
        elif self.current_step == 1:
            # ArrangementScreen validation
            pass
        elif self.current_step == 2:
            # SaveUploadScreen validation
            pass
        
    def build(self):
        """Build and return the main layout"""
        # TODO: Initialize screen instances with callbacks
        # TODO: Create stepper indicator (Step 1/2/3)
        match self.current_step:
            case 0:
                content = SelectionScreen(page=self.page).build()
            case 1:
                content = ArrangementScreen().build()
            case 2:
                content = SaveUploadScreen().build()
        # TODO: Display current screen based on self.current_step
        # TODO: Add settings button to open ConfigTab dialog
        
        # Stepper indicator
        stepper = ft.Container(
            content=ft.Row([
                # Step 1: Select Videos
                ft.Column([
                    ft.Container(
                        content=ft.Text("1", color=ft.Colors.WHITE),  # Number in circle
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.BLUE,  # Circle color
                        border_radius=20,  # Half of width/height = circle!
                        alignment=ft.alignment.center,
                    ),
                    ft.Text("Select Videos", size=12),  # Label below
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                ),
                
                ft.Container(  # Line
                    height=2,  # Thin line
                    bgcolor=ft.Colors.GREY,
                    expand=True,  # Stretch
                ),
                
                # Step 2: Arrange and Merge
                ft.Column([
                    ft.Container(
                        content=ft.Text("2", color=ft.Colors.WHITE),  # Number in circle
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.GREY,  # Circle color
                        border_radius=20,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text("Arrange and Merge", size=12),  # Label below
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                ),
                
                ft.Container(  # Line
                    height=2,
                    bgcolor=ft.Colors.GREY,
                    expand=True,  # Stretch
                ),
                
                # Step 3: Save/Upload
                ft.Column([
                    ft.Container(
                        content=ft.Text("3", color=ft.Colors.WHITE),  # Number in circle
                        width=40,
                        height=40,
                        bgcolor=ft.Colors.GREY,  # Circle color
                        border_radius=20,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text("Save/Upload", size=12),  # Label below
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(top=20, left=200, right=200), # Padding for the entire stepper indicator
        )
    
        # Fixed next button at bottom right
        self.next_button = ft.Container(
            content=ft.ElevatedButton(
                text="Next",
                icon=ft.Icons.ARROW_FORWARD,
                on_click=self.next_button_clicked,
            ),
            right=40,
            bottom=40,
        )
        
        return ft.Stack(
            [
                ft.Column(
                    [
                        stepper,
                        ft.Divider(),
                        content,
                    ],
                    expand=True,
                ),
                self.next_button,  # Fixed position overlay
            ],
            expand=True,
        )
