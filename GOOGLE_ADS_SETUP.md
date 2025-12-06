
# Google Ads Integration Guide

This document explains how to set up and configure Google AdSense ads in the Video Merger App for guest users.

## Overview

Google Ads are integrated via WebView to monetize the application for guest users. Ads are **only shown to guest users** and not to authenticated users, maintaining a premium experience for subscribers.

## Features

- **Automatic Ad Management**: Ads automatically show/hide based on user role
- **Multiple Ad Formats**: Support for banner, rectangle, and sidebar ads
- **Easy Configuration**: Simple setup with Google AdSense Publisher ID and Ad Slot IDs
- **Guest-Only Display**: Ads only appear for guest/free tier users
- **Responsive Design**: Ads integrate seamlessly with the UI

## Setup Instructions

### Step 1: Create Google AdSense Account

1. Visit [Google AdSense](https://www.google.com/adsense/)
2. Sign in with your Google account
3. Follow the setup wizard to create your account
4. Verify your website/application

### Step 2: Get Your Publisher ID

1. In AdSense dashboard, go to **Settings** → **Account**
2. Look for your **Publisher ID** (format: `ca-pub-XXXXXXXXXXXXXXXX`)
3. Copy this ID - you'll need it for configuration

### Step 3: Create Ad Units

1. In AdSense dashboard, go to **Ads** → **Ad Units**
2. Click **Create new ad unit**
3. Create the following ad units:

#### Required Ad Units:

1. **Horizontal Banner (Leaderboard)**
   - Size: 728x90
   - Name: `horizontal_banner`
   - Note the **Ad Unit ID** (Slot ID)

2. **Rectangle (Medium Rectangle)**
   - Size: 300x250
   - Name: `rectangle`
   - Note the **Ad Unit ID** (Slot ID)

3. **Vertical Sidebar (Wide Skyscraper)**
   - Size: 300x600
   - Name: `vertical_sidebar`
   - Note the **Ad Unit ID** (Slot ID)

### Step 4: Configure in Application

#### File: `src/app/services/google_ads_service.py`

1. Replace the placeholder Publisher ID:
```python
PUBLISHER_ID = "ca-pub-XXXXXXXXXXXXXXXX"  # Replace with your actual ID
```

2. Update the Ad Slots with your actual Ad Unit IDs:
```python
AD_SLOTS = {
    "horizontal_banner": {
        "slot_id": "YOUR_HORIZONTAL_SLOT_ID",  # Replace this
        "width": 728,
        "height": 90,
    },
    "vertical_sidebar": {
        "slot_id": "YOUR_VERTICAL_SLOT_ID",  # Replace this
        "width": 300,
        "height": 600,
    },
    "rectangle": {
        "slot_id": "YOUR_RECTANGLE_SLOT_ID",  # Replace this
        "width": 300,
        "height": 250,
    },
    "leaderboard": {
        "slot_id": "YOUR_LEADERBOARD_SLOT_ID",  # Replace this
        "width": 970,
        "height": 90,
    },
}
```

## Usage in Code

### Checking if Ads Should Display

```python
from app.services.ads_manager import should_show_ads

if should_show_ads():
    # Ads will be shown for this user
    ad = get_rectangle_ad()
```

### Adding Ads to Screens

The ads are already integrated in the following screens:

1. **Selection Screen** (`src/app/gui/selection_screen.py`)
   - Rectangle ad on the right side

2. **Arrangement Screen** (`src/app/gui/arrangement_screen.py`)
   - Horizontal banner at the top

3. **Save/Upload Screen** (`src/app/gui/save_upload_screen.py`)
   - Horizontal banner at the top

### Manual Ad Placement

To add ads to custom screens:

```python
from app.services.ads_manager import AdsManager

# Get specific ad
banner_ad = AdsManager.get_top_banner()
rectangle_ad = AdsManager.get_rectangle_ad()
sidebar_ad = AdsManager.get_sidebar_ad()

# Wrap content with ads
wrapped_content = AdsManager.wrap_with_ads(your_content, position="bottom")
```

### Available Methods

#### GoogleAdsService

- `create_ad_webview(ad_slot_key, width, height, on_ad_loaded)` - Create WebView with ad
- `create_ad_container(ad_slot_key, on_ad_loaded)` - Create Container with ad
- `is_publisher_id_configured()` - Check if configured
- `get_setup_instructions()` - Get setup help text

#### GuestAdManager

- `should_show_ads()` - Check if ads should display
- `get_ad_banner()` - Get banner ad
- `get_ad_rectangle()` - Get rectangle ad
- `get_ad_sidebar()` - Get sidebar ad
- `wrap_content_with_ads(content, position)` - Wrap with ads

#### AdsManager (Singleton)

- `should_show_ads()` - Global check
- `get_top_banner()` - Get banner
- `get_rectangle_ad()` - Get rectangle
- `get_sidebar_ad()` - Get sidebar
- `wrap_with_ads(content, position)` - Wrap content

## How It Works

### 1. Ad Detection

When a guest user logs in:
- `session_manager.is_guest` is checked
- `GoogleAdsService.is_publisher_id_configured()` verifies setup
- Ads are enabled only if both conditions are true

### 2. WebView Integration

Each ad is rendered via:
- HTML content with Google AdSense script tags
- Base64 encoded for security
- Flet's WebView component for display

### 3. Screen Integration

Each screen checks `should_show_ads()`:
- If `True`: Ads are added to the layout
- If `False`: Only content is shown (for authenticated users)

## Testing Ads Locally

### Ad Preview Mode

Google AdSense doesn't show real ads during development. Instead:

1. Use **Test Ad IDs** (if available in your AdSense account)
2. Or wait for account approval to see live ads
3. Ads will display as placeholders initially

### Test Cases

1. **Guest User** → Ads should appear
2. **Authenticated User** → Ads should NOT appear
3. **Different Screens** → Ads should appear in correct positions

## Troubleshooting

### Ads Not Showing

1. **Check Publisher ID**
   ```python
   from app.services.google_ads_service import GoogleAdsService
   print(GoogleAdsService.PUBLISHER_ID)
   ```

2. **Verify Ad Slot IDs**
   - Make sure slot IDs match AdSense account exactly

3. **Check User Role**
   ```python
   from access_control.session import session_manager
   print(f"Is guest: {session_manager.is_guest}")
   ```

4. **Check Configuration**
   ```python
   from app.services.google_ads_service import GoogleAdsService
   print(f"Configured: {GoogleAdsService.is_publisher_id_configured()}")
   ```

### WebView Issues

- Ensure Flet and WebView dependencies are installed
- Check browser console for JavaScript errors
- Verify internet connection (ads require network)

### AdSense Account Issues

- Wait for AdSense account approval (usually 24-48 hours)
- Check AdSense dashboard for policy violations
- Review site should have meaningful content

## Important Notes

⚠️ **For Production:**
- Only show ads to guest users
- Ensure your app complies with AdSense policies
- Monitor ad performance in AdSense dashboard
- Don't click your own ads
- Don't incentivize clicking ads

⚠️ **AdSense Policies:**
- Ads require real, valuable content
- Don't show excessive ads
- Respect user privacy
- Comply with all AdSense guidelines

## Revenue Optimization

1. **Ad Placement**: Ads in selection screen (rectangle) get better CTR
2. **Multiple Formats**: Test different sizes to find best fit
3. **Content Relevance**: Better content = higher CPM
4. **Traffic Quality**: Genuine users = better revenue

## Resources

- [Google AdSense Help](https://support.google.com/adsense/)
- [AdSense Policies](https://support.google.com/adsense/answer/48182)
- [Ad Formats Guide](https://support.google.com/adsense/answer/185665)
- [AdSense Blog](https://adsense.googleblog.com/)

## Questions?

For issues with ad integration:
1. Check the error logs
2. Verify configuration in `google_ads_service.py`
3. Review AdSense account status
4. Test with a fresh guest login

