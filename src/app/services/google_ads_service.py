"""
Google Ads Service
Handles Google AdSense integration via WebView for monetizing guest instances
"""

import flet as ft
from typing import Optional, Callable


class GoogleAdsService:
    """Service to integrate Google AdSense ads via WebView in Flet"""
    
    # Google AdSense Publisher ID - Replace with your actual publisher ID
    PUBLISHER_ID = "ca-pub-xxxxxxxxxxxxxxxx"
    
    # Ad slot configurations
    AD_SLOTS = {
        "horizontal_banner": {
            "slot_id": "1234567890",  # Replace with actual ad slot ID
            "width": 728,
            "height": 90,
        },
        "vertical_sidebar": {
            "slot_id": "0987654321",  # Replace with actual ad slot ID
            "width": 300,
            "height": 600,
        },
        "rectangle": {
            "slot_id": "1122334455",  # Replace with actual ad slot ID
            "width": 300,
            "height": 250,
        },
        "leaderboard": {
            "slot_id": "5566778899",  # Replace with actual ad slot ID
            "width": 970,
            "height": 90,
        },
    }
    
    @staticmethod
    def create_ad_webview(
        ad_slot_key: str = "rectangle",
        width: int = 300,
        height: int = 250,
        on_ad_loaded: Optional[Callable] = None
    ) -> ft.WebView:
        """
        Create a WebView containing a Google AdSense ad
        
        Args:
            ad_slot_key: Key from AD_SLOTS dictionary (default: 'rectangle')
            width: Width of ad container (px)
            height: Height of ad container (px)
            on_ad_loaded: Callback when ad loads
            
        Returns:
            ft.WebView with Google AdSense ad
        """
        
        # Get ad slot configuration
        ad_config = GoogleAdsService.AD_SLOTS.get(ad_slot_key, GoogleAdsService.AD_SLOTS["rectangle"])
        slot_id = ad_config["slot_id"]
        
        # HTML content for AdSense ad
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={GoogleAdsService.PUBLISHER_ID}"
                    crossorigin="anonymous"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background: transparent;
                    font-family: Arial, sans-serif;
                }}
                .ad-container {{
                    background: transparent;
                }}
            </style>
        </head>
        <body>
            <div class="ad-container">
                <ins class="adsbygoogle"
                     style="display:inline-block;width:{width}px;height:{height}px"
                     data-ad-client="{GoogleAdsService.PUBLISHER_ID}"
                     data-ad-slot="{slot_id}"></ins>
                <script>
                    (adsbygoogle = window.adsbygoogle || []).push({{}});
                </script>
            </div>
        </body>
        </html>
        """
        
        # Create WebView
        webview = ft.WebView(
            src_base64=GoogleAdsService._encode_html_to_base64(html_content),
            width=width,
            height=height,
            expand=False,
        )
        
        if on_ad_loaded:
            on_ad_loaded()
        
        return webview
    
    @staticmethod
    def _encode_html_to_base64(html_content: str) -> str:
        """
        Encode HTML content to base64 for WebView src_base64
        
        Args:
            html_content: HTML string
            
        Returns:
            Base64 encoded data URI
        """
        import base64
        encoded = base64.b64encode(html_content.encode()).decode()
        return f"data:text/html;base64,{encoded}"
    
    @staticmethod
    def create_ad_container(
        ad_slot_key: str = "rectangle",
        on_ad_loaded: Optional[Callable] = None
    ) -> ft.Container:
        """
        Create a Container with Google AdSense ad
        
        Args:
            ad_slot_key: Key from AD_SLOTS dictionary
            on_ad_loaded: Callback when ad loads
            
        Returns:
            ft.Container with ad
        """
        
        ad_config = GoogleAdsService.AD_SLOTS.get(ad_slot_key, GoogleAdsService.AD_SLOTS["rectangle"])
        width = ad_config["width"]
        height = ad_config["height"]
        
        webview = GoogleAdsService.create_ad_webview(ad_slot_key, width, height, on_ad_loaded)
        
        return ft.Container(
            content=webview,
            width=width,
            height=height,
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.05, "#FFFFFF"),
            padding=5,
        )
    
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
        
        return GoogleAdsService.create_ad_container("horizontal_banner")
    
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
