"""
Ads Manager Module
Central point for managing ads throughout the guest instance
"""

from app.services.google_ads_service import GoogleAdsService, GuestAdManager
from access_control.session import session_manager


class AdsManager:
    """
    Global ads manager singleton for the application
    Automatically enables/disables ads based on user role
    """
    
    _instance = None
    _ad_manager = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize ads manager"""
        if AdsManager._ad_manager is None:
            is_guest = session_manager.is_guest
            AdsManager._ad_manager = GuestAdManager(is_guest=is_guest)
    
    @staticmethod
    def should_show_ads() -> bool:
        """Check if ads should be shown for current user"""
        manager = AdsManager()
        return manager._ad_manager.should_show_ads()
    
    @staticmethod
    def get_top_banner() -> object:
        """Get top banner ad"""
        manager = AdsManager()
        return manager._ad_manager.get_ad_banner()
    
    @staticmethod
    def get_rectangle_ad() -> object:
        """Get rectangle ad (300x250)"""
        manager = AdsManager()
        return manager._ad_manager.get_ad_rectangle()
    
    @staticmethod
    def get_sidebar_ad() -> object:
        """Get sidebar ad (300x600)"""
        manager = AdsManager()
        return manager._ad_manager.get_ad_sidebar()
    
    @staticmethod
    def wrap_with_ads(content, position: str = "bottom") -> object:
        """
        Wrap content with ads
        
        Args:
            content: Main content control
            position: Ad position ('top', 'bottom', 'sides')
            
        Returns:
            Content wrapped with ads or original content if ads disabled
        """
        manager = AdsManager()
        return manager._ad_manager.wrap_content_with_ads(content, position)
    
    @staticmethod
    def get_publisher_info() -> str:
        """Get Google Publisher ID info"""
        if GoogleAdsService.is_publisher_id_configured():
            return "Google Ads configured"
        else:
            return GoogleAdsService.get_setup_instructions()


# Module-level convenience functions
def should_show_ads() -> bool:
    """Check if ads should be shown"""
    return AdsManager.should_show_ads()


def get_banner_ad():
    """Get banner ad for guest users"""
    return AdsManager.get_top_banner()


def get_rectangle_ad():
    """Get rectangle ad"""
    return AdsManager.get_rectangle_ad()


def get_sidebar_ad():
    """Get sidebar ad"""
    return AdsManager.get_sidebar_ad()


def wrap_with_ads(content, position: str = "bottom"):
    """Wrap content with ads"""
    return AdsManager.wrap_with_ads(content, position)
