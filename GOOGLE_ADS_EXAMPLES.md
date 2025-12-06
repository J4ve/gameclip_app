# Google Ads Integration Examples

This file contains practical examples of how to use the Google Ads system in your Video Merger App.

## Basic Usage

### Example 1: Check if Ads Should Display

```python
from app.services.ads_manager import should_show_ads

if should_show_ads():
    print("Showing ads to guest user")
else:
    print("User is authenticated - no ads")
```

### Example 2: Add Banner Ad to Your Screen

```python
from app.services.ads_manager import AdsManager
import flet as ft

def build_my_screen():
    main_content = ft.Column([
        ft.Text("My Screen Content"),
        ft.Text("Some other content here"),
    ])
    
    # Option 1: Get banner directly
    if AdsManager.should_show_ads():
        banner = AdsManager.get_top_banner()
        if banner:
            content = ft.Column([
                banner,
                main_content,
            ])
        else:
            content = main_content
    else:
        content = main_content
    
    return content
```

### Example 3: Add Rectangle Ad Next to Content

```python
from app.services.ads_manager import AdsManager
import flet as ft

def build_screen_with_sidebar():
    main_content = ft.Column([
        ft.Text("Main content here"),
        ft.TextField(label="Enter something"),
    ], expand=True)
    
    layout = ft.Row([
        main_content,
    ], spacing=20)
    
    # Add ad on the right for guests
    if AdsManager.should_show_ads():
        ad = AdsManager.get_rectangle_ad()
        if ad:
            layout.controls.append(ad)
    
    return layout
```

### Example 4: Wrap Content with Ads

```python
from app.services.ads_manager import AdsManager
import flet as ft

def build_screen():
    content = ft.Column([
        ft.Text("Content here"),
        ft.Button("Do something"),
    ])
    
    # Automatically wrap with ads if needed
    return AdsManager.wrap_with_ads(content, position="bottom")
```

## Advanced Usage

### Example 5: Custom Ad Placement

```python
from app.services.google_ads_service import GoogleAdsService
import flet as ft

def build_custom_layout():
    # Create a specific ad
    ad = GoogleAdsService.create_ad_container("horizontal_banner")
    
    content = ft.Column([
        ft.Text("Header"),
        ad,  # Ad in middle
        ft.Text("Content after ad"),
    ])
    
    return content
```

### Example 6: Ad with Callback

```python
from app.services.google_ads_service import GoogleAdsService

def on_ad_loaded():
    print("Ad has been loaded!")

def build_with_callback():
    ad = GoogleAdsService.create_ad_webview(
        ad_slot_key="rectangle",
        on_ad_loaded=on_ad_loaded
    )
    
    return ad
```

### Example 7: Check Configuration Status

```python
from app.services.google_ads_service import GoogleAdsService

def check_ads_setup():
    if GoogleAdsService.is_publisher_id_configured():
        print("✓ Google Ads is properly configured")
    else:
        print("✗ Google Ads is NOT configured")
        print(GoogleAdsService.get_setup_instructions())
```

### Example 8: Get Different Ad Sizes

```python
from app.services.ads_manager import AdsManager

def display_various_ads():
    banner = AdsManager.get_top_banner()      # 728x90
    rectangle = AdsManager.get_rectangle_ad()  # 300x250
    sidebar = AdsManager.get_sidebar_ad()      # 300x600
    
    return {
        'banner': banner,
        'rectangle': rectangle,
        'sidebar': sidebar
    }
```

## Real-World Scenarios

### Scenario 1: Add Ads Only to Guest Selection Screen

```python
# In selection_screen.py
from app.services.ads_manager import should_show_ads, get_rectangle_ad
import flet as ft

class SelectionScreen:
    def build(self):
        main_content = ft.Column([
            ft.Text("Select Videos"),
            # ... rest of UI
        ])
        
        # Add ad for guests
        if should_show_ads():
            ad = get_rectangle_ad()
            if ad:
                return ft.Row([
                    main_content,
                    ad,
                ], spacing=20)
        
        return main_content
```

### Scenario 2: Conditional Ad Display Based on Screen

```python
# In main_window.py
from app.services.ads_manager import AdsManager
import flet as ft

class MainWindow:
    def build(self):
        current_screen = self.get_current_screen()
        
        if AdsManager.should_show_ads():
            # Different ads for different screens
            if self.current_step == 0:  # Selection
                ad_placement = "right"
            elif self.current_step == 1:  # Arrangement
                ad_placement = "top"
            else:  # Save/Upload
                ad_placement = "top"
        
        # Build screen with appropriate ad placement
        return self.build_screen(ad_placement)
```

### Scenario 3: Track Ad Performance

```python
from app.services.ads_manager import should_show_ads, AdsManager

class AnalyticsTracker:
    def track_guest_interaction(self):
        if should_show_ads():
            print("Guest user with ads enabled")
            # Track in analytics
            self.log_event("ads_visible", {
                "user_type": "guest",
                "ads_enabled": True
            })
```

### Scenario 4: Premium User Experience (No Ads)

```python
from access_control.session import session_manager
import flet as ft

def build_premium_screen():
    main_content = ft.Column([
        ft.Text("Premium content - Ad-free experience!"),
        # ... premium features
    ])
    
    # Authenticated users never see ads
    if not session_manager.is_guest:
        return main_content
    
    # Guest users might see ads
    from app.services.ads_manager import AdsManager
    return AdsManager.wrap_with_ads(main_content, "bottom")
```

## Integration Patterns

### Pattern 1: Service Initialization

```python
# At app startup
from app.services.ads_manager import AdsManager

def initialize_app():
    # Singleton automatically initializes based on user role
    ads_manager = AdsManager()
    
    if ads_manager.should_show_ads():
        print("Ads enabled for this session")
```

### Pattern 2: Lazy Ad Loading

```python
from app.services.ads_manager import should_show_ads, get_banner_ad

def build_expensive_screen():
    content = ft.Column([
        # Build main content first
        build_main_content(),
    ])
    
    # Load ads only if needed
    if should_show_ads():
        ad = get_banner_ad()
        if ad:
            content.controls.insert(0, ad)
    
    return content
```

### Pattern 3: Ad Fallback

```python
from app.services.ads_manager import AdsManager
import flet as ft

def build_with_fallback():
    ad = AdsManager.get_rectangle_ad()
    
    # Graceful fallback if ad fails to load
    if ad is None:
        ad_placeholder = ft.Container(
            content=ft.Text("Ad space available"),
            width=300,
            height=250,
            bgcolor=ft.Colors.GREY_800,
            border_radius=8,
        )
    else:
        ad_placeholder = ad
    
    return ft.Row([
        ft.Text("Main content"),
        ad_placeholder,
    ])
```

### Pattern 4: User Role Detection

```python
from access_control.session import session_manager
from app.services.ads_manager import AdsManager

def render_based_on_role():
    if session_manager.is_guest:
        # Show guest version with ads
        content = AdsManager.wrap_with_ads(guest_content(), "bottom")
        return content
    else:
        # Show premium version without ads
        return premium_content()
```

## Testing Ads Locally

### Test 1: Verify Guest Ad Display

```python
# Login as guest, then check:
from app.services.ads_manager import should_show_ads
from access_control.session import session_manager

print(f"Is guest: {session_manager.is_guest}")
print(f"Should show ads: {should_show_ads()}")
print(f"Ad slots configured: {len(GoogleAdsService.AD_SLOTS)}")
```

### Test 2: Verify Authenticated User No Ads

```python
# Login with Google, then check:
from app.services.ads_manager import should_show_ads
from access_control.session import session_manager

print(f"Is guest: {session_manager.is_guest}")  # Should be False
print(f"Should show ads: {should_show_ads()}")   # Should be False
```

### Test 3: Configuration Check

```python
from app.services.google_ads_service import GoogleAdsService

# Check if properly configured
status = GoogleAdsService.is_publisher_id_configured()
print(f"Configured: {status}")

if not status:
    print(GoogleAdsService.get_setup_instructions())
```

## Common Issues and Solutions

### Issue: Ads Not Showing to Guest Users

**Solution 1**: Check configuration
```python
from app.services.google_ads_service import GoogleAdsService
if not GoogleAdsService.is_publisher_id_configured():
    print("Publisher ID not configured!")
```

**Solution 2**: Verify user is guest
```python
from access_control.session import session_manager
print(f"User role: {session_manager.current_role}")
print(f"Is guest: {session_manager.is_guest}")
```

**Solution 3**: Check ads enabled
```python
from app.services.ads_manager import should_show_ads
if not should_show_ads():
    print("Ads are disabled for this user")
```

### Issue: Ads Showing to Authenticated Users

**Check session**:
```python
from access_control.session import session_manager
print(f"Current role: {session_manager.current_role}")
print(f"Email: {session_manager.email}")
```

### Issue: WebView Not Displaying

**Check WebView support**:
```python
import flet as ft
# Verify WebView is available
print("WebView supported on this platform")
```

## Performance Tips

1. **Cache ads**: Create once, reuse multiple times
2. **Lazy load**: Load ads only when needed
3. **Conditional rendering**: Don't create ad objects for authenticated users
4. **Proper cleanup**: Remove ads from layout when switching screens

## Production Checklist

- [ ] Publisher ID configured in `google_ads_service.py`
- [ ] All ad slot IDs are correct
- [ ] Ads show only for guest users
- [ ] Ads hide for authenticated users
- [ ] No ads during development/testing
- [ ] Ad placement is non-intrusive
- [ ] Performance is not impacted
- [ ] Tested on web, desktop, mobile
- [ ] AdSense policies reviewed
- [ ] Terms of service accepted

## Additional Resources

- Main implementation: `src/app/services/google_ads_service.py`
- Manager service: `src/app/services/ads_manager.py`
- Setup guide: `GOOGLE_ADS_SETUP.md`
- Implementation guide: `GOOGLE_ADS_IMPLEMENTATION.md`
