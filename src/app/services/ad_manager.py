"""
Ad Manager - Handles ad rotation, timing, and Image-based ad display
Supports customizable ad rotation from config file
"""

import flet as ft
import random
import threading
import time
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from access_control.session import session_manager
import webbrowser


class AdConfig:
    """Configuration for ad behavior"""
    # Ad rotation settings
    ROTATION_ORDER = "random"  # Options: "random", "sequential"
    ROTATION_INTERVAL = 10  # seconds between ad changes
    
    # Ad config file path
    CONFIG_FILE = Path(__file__).parent.parent.parent.parent / "configs" / "ad_config.txt"
    
    # Default fallback ad
    DEFAULT_AD = ("https://via.placeholder.com/728x90.png?text=Advertisement", "https://example.com")


class AdManager:
    """Manages ad display, rotation, and click tracking"""
    
    def __init__(self):
        self.horizontal_ads: List[Tuple[str, str]] = []  # List of (image_url, redirect_url) for horizontal
        self.vertical_ads: List[Tuple[str, str]] = []  # List of (image_url, redirect_url) for vertical
        self.current_horizontal_index = 0
        self.current_vertical_index = 0
        self.rotation_thread: Optional[threading.Thread] = None
        self.should_rotate = False
        self.webview_callbacks: List[Callable] = []  # Callbacks to update WebView
        
        self._load_ads()
    
    def _load_ads(self):
        """Load ads from config file, separating horizontal and vertical"""
        try:
            if AdConfig.CONFIG_FILE.exists():
                current_section = None
                with open(AdConfig.CONFIG_FILE, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue
                        
                        # Check for section headers
                        if line == '[HORIZONTAL]':
                            current_section = 'horizontal'
                            continue
                        elif line == '[VERTICAL]':
                            current_section = 'vertical'
                            continue
                        
                        # Parse format: image_url|redirect_url
                        if '|' in line:
                            parts = line.split('|', 1)
                            if len(parts) == 2:
                                ad_entry = (parts[0].strip(), parts[1].strip())
                                if current_section == 'horizontal':
                                    self.horizontal_ads.append(ad_entry)
                                elif current_section == 'vertical':
                                    self.vertical_ads.append(ad_entry)
                        else:
                            # If no redirect URL, use image URL as redirect
                            ad_entry = (line.strip(), line.strip())
                            if current_section == 'horizontal':
                                self.horizontal_ads.append(ad_entry)
                            elif current_section == 'vertical':
                                self.vertical_ads.append(ad_entry)
            
            # If no ads loaded, use defaults
            if not self.horizontal_ads:
                self.horizontal_ads.append(AdConfig.DEFAULT_AD)
                print("No horizontal ads found in config, using default ad")
            else:
                print(f"Loaded {len(self.horizontal_ads)} horizontal ads from config")
            
            if not self.vertical_ads:
                self.vertical_ads.append(AdConfig.DEFAULT_AD)
                print("No vertical ads found in config, using default ad")
            else:
                print(f"Loaded {len(self.vertical_ads)} vertical ads from config")
                
        except Exception as e:
            print(f"Error loading ads: {e}")
            self.horizontal_ads.append(AdConfig.DEFAULT_AD)
            self.vertical_ads.append(AdConfig.DEFAULT_AD)
    
    def should_show_ads(self) -> bool:
        """Check if current user should see ads"""
        return session_manager.has_ads()
    
    def get_current_horizontal_ad(self) -> Tuple[str, str]:
        """Get current horizontal ad (image_url, redirect_url)"""
        if not self.horizontal_ads:
            return AdConfig.DEFAULT_AD
        return self.horizontal_ads[self.current_horizontal_index]
    
    def get_current_vertical_ad(self) -> Tuple[str, str]:
        """Get current vertical ad (image_url, redirect_url)"""
        if not self.vertical_ads:
            return AdConfig.DEFAULT_AD
        return self.vertical_ads[self.current_vertical_index]
    
    def get_next_horizontal_ad(self) -> Tuple[str, str]:
        """Move to next horizontal ad and return it"""
        if not self.horizontal_ads:
            return AdConfig.DEFAULT_AD
        
        if AdConfig.ROTATION_ORDER == "random":
            # Random selection (avoid showing same ad twice in a row if possible)
            if len(self.horizontal_ads) > 1:
                new_index = self.current_horizontal_index
                while new_index == self.current_horizontal_index:
                    new_index = random.randint(0, len(self.horizontal_ads) - 1)
                self.current_horizontal_index = new_index
            else:
                self.current_horizontal_index = 0
        else:  # sequential
            self.current_horizontal_index = (self.current_horizontal_index + 1) % len(self.horizontal_ads)
        
        return self.horizontal_ads[self.current_horizontal_index]
    
    def get_next_vertical_ad(self) -> Tuple[str, str]:
        """Move to next vertical ad and return it"""
        if not self.vertical_ads:
            return AdConfig.DEFAULT_AD
        
        if AdConfig.ROTATION_ORDER == "random":
            # Random selection (avoid showing same ad twice in a row if possible)
            if len(self.vertical_ads) > 1:
                new_index = self.current_vertical_index
                while new_index == self.current_vertical_index:
                    new_index = random.randint(0, len(self.vertical_ads) - 1)
                self.current_vertical_index = new_index
            else:
                self.current_vertical_index = 0
        else:  # sequential
            self.current_vertical_index = (self.current_vertical_index + 1) % len(self.vertical_ads)
        
        return self.vertical_ads[self.current_vertical_index]
    
    def register_update_callback(self, callback: Callable):
        """Register a callback to be called when ad should update"""
        if callback not in self.webview_callbacks:
            self.webview_callbacks.append(callback)
    
    def unregister_update_callback(self, callback: Callable):
        """Unregister an update callback"""
        if callback in self.webview_callbacks:
            self.webview_callbacks.remove(callback)
    
    def _rotation_worker(self):
        """Background thread that triggers ad rotation"""
        while self.should_rotate:
            time.sleep(AdConfig.ROTATION_INTERVAL)
            if self.should_rotate:
                self.get_next_horizontal_ad()
                self.get_next_vertical_ad()
                # Notify all registered callbacks
                for callback in self.webview_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        print(f"Error in ad update callback: {e}")
    
    def start_rotation(self):
        """Start automatic ad rotation"""
        if not self.should_rotate and (len(self.horizontal_ads) > 1 or len(self.vertical_ads) > 1):
            self.should_rotate = True
            self.rotation_thread = threading.Thread(target=self._rotation_worker, daemon=True)
            self.rotation_thread.start()
            print("Ad rotation started")
    
    def stop_rotation(self):
        """Stop automatic ad rotation"""
        self.should_rotate = False
        if self.rotation_thread:
            self.rotation_thread = None
        print("Ad rotation stopped")
    
    def _handle_ad_click(self, redirect_url: str):
        """Handle ad click - open URL in browser"""
        try:
            webbrowser.open(redirect_url)
        except Exception as e:
            print(f"Error opening ad URL: {e}")
    
    def create_horizontal_ad(self, page: ft.Page, width: int = 300, height: int = 250) -> ft.Container:
        """
        Create a horizontal ad container for side placement
        
        Args:
            page: Flet page instance
            width: Ad width
            height: Ad height
        
        Returns:
            Container with Image ad
        """
        if not self.should_show_ads():
            return ft.Container(visible=False)
        
        image_url, redirect_url = self.get_current_horizontal_ad()
        
        ad_image = ft.Image(
            src=image_url,
            width=width,
            height=height,
            fit=ft.ImageFit.CONTAIN,
            border_radius=8,
        )
        
        def update_ad():
            """Update the ad content"""
            try:
                new_image_url, new_redirect_url = self.get_current_horizontal_ad()
                ad_image.src = new_image_url
                clickable_container.data = new_redirect_url
                if page:
                    page.update()
            except Exception as e:
                print(f"Error updating horizontal ad: {e}")
        
        self.register_update_callback(update_ad)
        
        clickable_container = ft.Container(
            content=ad_image,
            data=redirect_url,  # Store redirect URL in data
            on_click=lambda e: self._handle_ad_click(e.control.data),
            tooltip="Click to learn more",
            ink=True,
            border_radius=8,
        )
        
        return ft.Container(
            content=clickable_container,
            width=width,
            height=height,
            bgcolor=ft.Colors.with_opacity(0.05, "#1a1a1a"),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#FFFFFF")),
            padding=5,
        )
    
    def create_vertical_banner_ad(self, page: ft.Page, width: int = 728, height: int = 90) -> ft.Container:
        """
        Create a vertical banner ad for top placement
        
        Args:
            page: Flet page instance
            width: Ad width
            height: Ad height
        
        Returns:
            Container with Image ad
        """
        if not self.should_show_ads():
            return ft.Container(visible=False)
        
        image_url, redirect_url = self.get_current_vertical_ad()
        
        ad_image = ft.Image(
            src=image_url,
            width=width,
            height=height,
            fit=ft.ImageFit.CONTAIN,
            border_radius=8,
        )
        
        def update_ad():
            """Update the ad content"""
            try:
                new_image_url, new_redirect_url = self.get_current_vertical_ad()
                ad_image.src = new_image_url
                clickable_container.data = new_redirect_url
                if page:
                    page.update()
            except Exception as e:
                print(f"Error updating banner ad: {e}")
        
        self.register_update_callback(update_ad)
        
        clickable_container = ft.Container(
            content=ad_image,
            data=redirect_url,  # Store redirect URL in data
            on_click=lambda e: self._handle_ad_click(e.control.data),
            tooltip="Click to learn more",
            ink=True,
            border_radius=8,
        )
        
        return ft.Container(
            content=clickable_container,
            width=width,
            height=height,
            bgcolor=ft.Colors.with_opacity(0.05, "#1a1a1a"),
            border_radius=8,
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#FFFFFF")),
            padding=5,
            margin=ft.margin.only(bottom=10),
        )


# Global ad manager instance
ad_manager = AdManager()

# Export
__all__ = ['AdManager', 'AdConfig', 'ad_manager']
