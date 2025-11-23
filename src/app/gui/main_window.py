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
        self.current_step = 0  # 0=Upload, 1=Arrange, 2=Save/Upload
        self.selected_videos = []  # Shared state across screens
        self.setup_page()
        
    def setup_page(self):
        """Configure page settings"""
        self.page.title = Config.APP_TITLE
        self.page.window_width = Config.APP_WIDTH
        self.page.window_height = Config.APP_HEIGHT
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
        
    def build(self):
        """Build and return the main layout"""
        # TODO: Initialize screen instances with callbacks
        # TODO: Create stepper indicator (Step 1/2/3)
        # TODO: Display current screen based on self.current_step
        # TODO: Add settings button to open ConfigTab dialog
        
        # Placeholder stepper indicator
        stepper = ft.Row(
            [
                ft.Text("Step 1: Select", weight=ft.FontWeight.BOLD),
                ft.Icon(ft.icons.ARROW_FORWARD),
                ft.Text("Step 2: Arrange"),
                ft.Icon(ft.icons.ARROW_FORWARD),
                ft.Text("Step 3: Save/Upload"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        # Placeholder for screen content
        content = ft.Container(
            content=ft.Text("Screen content goes here"),
            expand=True,
        )
        
        return ft.Column(
            [
                stepper,
                ft.Divider(),
                content,
            ],
            expand=True,
        )
