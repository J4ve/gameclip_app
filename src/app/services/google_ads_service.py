"""
Google Ads Service
Handles Google AdSense integration using native Flet components for monetizing guest instances
"""

import flet as ft
from typing import Optional, Callable
import webbrowser


class GoogleAdsService:
    """Service to integrate Google AdSense ads using native Flet components"""
    
    # Google AdSense Publisher ID
    PUBLISHER_ID = "pub-4777093929422930"
    
    # Ad slot configurations with details
    AD_SLOTS = {
        "horizontal_banner": {
            "slot_id": "5248104584",  # Banner (full-width x 40)
            "width": 728,
            "height": 90,
            "title": "Sponsored Content",
        },
        "vertical_sidebar": {
            "slot_id": "4196260255",  # Vertical Sidebar (300x600)
            "width": 300,
            "height": 600,
            "title": "Advertisement",
        },
        "rectangle": {
            "slot_id": "1308859573",  # Rectangle (300x250)
            "width": 300,
            "height": 250,
            "title": "Featured Ad",
        },
        "leaderboard": {
            "slot_id": "5248104584",  # Leaderboard (970x90)
            "width": 970,
            "height": 90,
            "title": "Sponsored Content",
        },
    }
    
    @staticmethod
    def create_native_ad(
        ad_slot_key: str = "rectangle",
        width: int = 300,
        height: int = 250,
        on_click: Optional[Callable] = None,
        expand: bool = False
    ) -> ft.Container:
        """
        Create a native Flet ad container with clickable areas
        This works on all platforms where WebView is not supported
        
        Args:
            ad_slot_key: Key from AD_SLOTS dictionary (default: 'rectangle')
            width: Width of ad container (px)
            height: Height of ad container (px)
            on_click: Callback when ad is clicked
            
        Returns:
            ft.Container with native ad design
        """
        
        # Get ad slot configuration
        ad_config = GoogleAdsService.AD_SLOTS.get(ad_slot_key, GoogleAdsService.AD_SLOTS["rectangle"])
        
        def handle_ad_click():
            """Handle ad click - open AdSense publisher page"""
            if on_click:
                on_click()
            # Open your AdSense page (users can see your ads and stats)
            webbrowser.open(f"https://www.google.com/adsense/")
        
        # Create an attractive ad container
        ad_container = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Ad",
                        size=7,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_600,
                    ),
                    ft.Divider(height=2, color="transparent"),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.ADS_CLICK,
                                    size=16,
                                    color=ft.Colors.BLUE_400,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            "Advertisement",
                                            size=8,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.ON_SURFACE,
                                        ),
                                    ],
                                    spacing=0,
                                    tight=True,
                                ),
                            ],
                            spacing=6,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        expand=False,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            width=None,
            height=height,
            expand=False,
            bgcolor=ft.Colors.with_opacity(0.02, "#CCCCCC"),
            border=ft.border.all(1, ft.Colors.with_opacity(0.2, "#DDDDDD")),
            border_radius=6,
            padding=6,
            ink=True,
            on_click=lambda e: handle_ad_click(),
        )
        
        return ad_container
    
    @staticmethod
    def create_ad_webview(
        ad_slot_key: str = "rectangle",
        width: int = 300,
        height: int = 250,
        on_ad_loaded: Optional[Callable] = None
    ) -> ft.Control:
        """
        Create an ad container - falls back to native ad since WebView not supported
        
        Args:
            ad_slot_key: Key from AD_SLOTS dictionary (default: 'rectangle')
            width: Width of ad container (px)
            height: Height of ad container (px)
            on_ad_loaded: Callback when ad loads
            
        Returns:
            ft.Control with ad (native implementation)
        """
        
        ad = GoogleAdsService.create_native_ad(ad_slot_key, width, height, on_ad_loaded)
        
        if on_ad_loaded:
            on_ad_loaded()
        
        return ad
    
    @staticmethod
    def create_ad_container(
        ad_slot_key: str = "rectangle",
        on_ad_loaded: Optional[Callable] = None,
        expand: bool = False
    ) -> ft.Container:
        """
        Create a Container with Google AdSense ad
        
        Args:
            ad_slot_key: Key from AD_SLOTS dictionary
            on_ad_loaded: Callback when ad loads
            expand: Whether the ad should expand to fill available space
            
        Returns:
            ft.Container with native ad
        """
        
        ad_config = GoogleAdsService.AD_SLOTS.get(ad_slot_key, GoogleAdsService.AD_SLOTS["rectangle"])
        width = ad_config["width"]
        height = ad_config["height"]
        
        # Use native ad instead of WebView
        return GoogleAdsService.create_native_ad(ad_slot_key, width, height, on_ad_loaded, expand)
    
    @staticmethod
    def is_publisher_id_configured() -> bool:
        """
        Check if Google Publisher ID is properly configured
        
        Returns:
            True if configured, False otherwise
        """
        return GoogleAdsService.PUBLISHER_ID != "ca-pub-xxxxxxxxxxxxxxxx"
    
    @staticmethod
    def get_setup_instructions() -> str:
        """
        Get setup instructions for configuring Google AdSense
        
        Returns:
            String with setup instructions
        """
        return """
        Google AdSense Setup Instructions:
        
        1. Visit https://www.google.com/adsense/
        2. Sign in with your Google account
        3. Get your Publisher ID (format: ca-pub-XXXXXXXXXXXXXXXX)
        4. Create ad units and get their Slot IDs
        5. Update PUBLISHER_ID and AD_SLOTS in google_ads_service.py
        6. Replace placeholder values with your actual IDs
        
        Important: Only show ads to guest users to avoid overwhelming premium users
        """


class GuestAdManager:
    """
    Manages ad placement for guest users throughout the application
    """
    
    def __init__(self, is_guest: bool = False):
        """
        Initialize ad manager
        
        Args:
            is_guest: Whether user is a guest
        """
        self.is_guest = is_guest
        self.ads_enabled = is_guest and GoogleAdsService.is_publisher_id_configured()
    
    def should_show_ads(self) -> bool:
        """Check if ads should be shown"""
        return self.ads_enabled
    
    def get_ad_banner(self) -> Optional[ft.Container]:
        """
        Get a horizontal banner ad for guest users
        
        Returns:
            Container with ad or None if ads disabled
        """
        if not self.should_show_ads():
            return None
        
        return GoogleAdsService.create_ad_container("horizontal_banner", expand=True)
    
    def get_ad_rectangle(self) -> Optional[ft.Container]:
        """
        Get a rectangle ad (300x250) for guest users
        
        Returns:
            Container with ad or None if ads disabled
        """
        if not self.should_show_ads():
            return None
        
        return GoogleAdsService.create_ad_container("rectangle")
    
    def get_ad_sidebar(self) -> Optional[ft.Container]:
        """
        Get a vertical sidebar ad (300x600) for guest users
        
        Returns:
            Container with ad or None if ads disabled
        """
        if not self.should_show_ads():
            return None
        
        return GoogleAdsService.create_ad_container("vertical_sidebar")
    
    def wrap_content_with_ads(
        self,
        main_content: ft.Control,
        ad_position: str = "bottom"  # 'top', 'bottom', 'sides'
    ) -> ft.Control:
        """
        Wrap main content with ads
        
        Args:
            main_content: The main content control
            ad_position: Where to place ads ('top', 'bottom', 'sides')
            
        Returns:
            Content control with ads placed
        """
        if not self.should_show_ads():
            return main_content
        
        ad_banner = GoogleAdsService.create_ad_container("horizontal_banner")
        
        if ad_position == "top":
            return ft.Column([
                ad_banner,
                ft.Divider(height=10),
                main_content,
            ], spacing=10)
        
        elif ad_position == "bottom":
            return ft.Column([
                main_content,
                ft.Divider(height=10),
                ad_banner,
            ], spacing=10)
        
        elif ad_position == "sides":
            ad_rectangle = GoogleAdsService.create_ad_container("rectangle")
            return ft.Row([
                main_content,
                ad_rectangle,
            ], spacing=10)
        
        return main_content
