# SETUP CHECKLIST - Google Ads Integration

Complete this checklist to get Google Ads working in your Video Merger App.

---

## 📋 PRE-INSTALLATION CHECK

- [x] Python 3.8+ installed
- [x] Flet installed (dependency already in requirements.txt)
- [x] Git initialized
- [x] Current branch: `feature/config-tab-fix`

**Status**: ✅ All prerequisites met

---

## 🔧 INSTALLATION COMPLETE

- [x] `src/app/services/google_ads_service.py` created
- [x] `src/app/services/ads_manager.py` created
- [x] `src/app/services/__init__.py` created
- [x] `src/app/gui/selection_screen.py` modified
- [x] `src/app/gui/arrangement_screen.py` modified
- [x] `src/app/gui/save_upload_screen.py` modified
- [x] All syntax verified
- [x] All imports tested
- [x] Documentation created

**Status**: ✅ Installation 100% complete

---

## 📝 CONFIGURATION NEEDED (You Must Do This)

### Phase 1: Google AdSense Account

**Required**: 5-10 minutes

- [ ] Go to https://www.google.com/adsense/
- [ ] Sign in with Google account (or create new account)
- [ ] Complete AdSense signup form
- [ ] Verify your identity (if needed)
- [ ] Wait for account approval (usually 24-48 hours)

**Note**: You'll need to wait for Google to review and approve your account before you can create ad units.

### Phase 2: Get Your Publisher ID

**Required**: Once account approved

- [ ] Go to AdSense Dashboard
- [ ] Click: Settings → Account → Publisher ID
- [ ] Copy your Publisher ID (format: `ca-pub-XXXXXXXXXXXXXXXX`)
- [ ] Save it somewhere safe

### Phase 3: Create Ad Units

**Required**: Once Publisher ID obtained

Create THREE ad units:

**Unit 1: Horizontal Banner**
- [ ] Go to: Ads → Ad Units → Create new ad unit
- [ ] Name: "Video Merger - Top Banner"
- [ ] Type: Display ad
- [ ] Size: Custom (728 x 90 px)
- [ ] Copy the Ad Unit ID / Slot ID
- [ ] Save: Will use as "horizontal_banner" slot_id

**Unit 2: Rectangle**
- [ ] Go to: Ads → Ad Units → Create new ad unit
- [ ] Name: "Video Merger - Rectangle"
- [ ] Type: Display ad
- [ ] Size: Medium rectangle (300 x 250 px)
- [ ] Copy the Ad Unit ID / Slot ID
- [ ] Save: Will use as "rectangle" slot_id

**Unit 3: Vertical Sidebar (Optional)**
- [ ] Go to: Ads → Ad Units → Create new ad unit
- [ ] Name: "Video Merger - Sidebar"
- [ ] Type: Display ad
- [ ] Size: Wide skyscraper (300 x 600 px)
- [ ] Copy the Ad Unit ID / Slot ID
- [ ] Save: Will use as "vertical_sidebar" slot_id

### Phase 4: Update Configuration File

**File**: `src/app/services/google_ads_service.py`

- [ ] Find line 15: `PUBLISHER_ID = "ca-pub-xxxxxxxxxxxxxxxx"`
- [ ] Replace `xxxxxxxxxxxxxxxx` with YOUR Publisher ID (the part after `ca-pub-`)
- [ ] Result should look like: `PUBLISHER_ID = "ca-pub-1a2b3c4d5e6f7g8h9i0j"`

- [ ] Find lines 19-34: `AD_SLOTS = {`
- [ ] Line 21: Replace `"1234567890"` with your horizontal_banner Slot ID
- [ ] Line 26: Replace `"0987654321"` with your rectangle Slot ID
- [ ] Line 31: Replace `"1122334455"` with your vertical_sidebar Slot ID (optional)
- [ ] Line 36: Replace `"5566778899"` with your leaderboard Slot ID (optional)

**Example** (what it should look like):
```python
PUBLISHER_ID = "ca-pub-2847d3b58c6f9e1a"

AD_SLOTS = {
    "horizontal_banner": {
        "slot_id": "4726594821",
        "width": 728,
        "height": 90,
    },
    "rectangle": {
        "slot_id": "3918572604",
        "width": 300,
        "height": 250,
    },
    # ... etc
}
```

- [ ] Save the file
- [ ] Check for any typos or errors

**Status**: ⏳ Waiting for you to complete this

---

## 🧪 TESTING

Once configuration is complete:

### Test 1: Verify Configuration

- [ ] Open PowerShell/Terminal
- [ ] Navigate to: `cd c:\Users\Marc\Desktop\Video\ Merger\ App\videomerger_app`
- [ ] Run: `python -c "from src.app.services.google_ads_service import GoogleAdsService; print(GoogleAdsService.is_publisher_id_configured())"`
- [ ] Should print: `True`

### Test 2: Test Guest User Ads

- [ ] Run the app: `python src/main.py`
- [ ] Click: "Or continue without signing in" (guest login)
- [ ] You should see:
  - [ ] Selection Screen: Rectangle ad (300x250) on right side
  - [ ] Arrangement Screen: Horizontal banner (728x90) at top
  - [ ] Save/Upload Screen: Horizontal banner (728x90) at top

### Test 3: Test Authenticated User (No Ads)

- [ ] Go back to login screen
- [ ] Click: "Sign in with Google"
- [ ] Complete Google OAuth login
- [ ] You should see:
  - [ ] Selection Screen: NO ads (only content)
  - [ ] Arrangement Screen: NO ads (only content)
  - [ ] Save/Upload Screen: NO ads (only content)

### Test 4: Verify Imports

- [ ] Open PowerShell/Terminal
- [ ] Run this Python code:
```python
import sys
sys.path.insert(0, r'c:\Users\Marc\Desktop\Video Merger App\videomerger_app\src')
from app.services.ads_manager import should_show_ads, get_banner_ad, get_rectangle_ad
print("All imports successful!")
```
- [ ] Should print: `All imports successful!`

---

## 📊 MONITORING

Once everything is working:

- [ ] Log in to AdSense dashboard daily for first week
- [ ] Monitor: Impressions (times ads are shown)
- [ ] Monitor: Clicks (times users click ads)
- [ ] Monitor: Earnings (revenue generated)
- [ ] Track: CTR (click-through rate)

---

## 🎯 GO-LIVE CHECKLIST

Before deploying to production:

- [ ] Configuration complete and tested locally
- [ ] All 3 screens show ads to guests
- [ ] No ads appear for authenticated users
- [ ] Ad placement looks good (not blocking content)
- [ ] No console errors or warnings
- [ ] Performance is acceptable
- [ ] Tested on multiple screen sizes
- [ ] AdSense policies reviewed
- [ ] Ready for live traffic

---

## ⚠️ IMPORTANT REMINDERS

### Policy Compliance
- [ ] Review AdSense policies before going live
- [ ] Don't click your own ads (violates policy)
- [ ] Don't incentivize users to click ads
- [ ] Maintain meaningful content
- [ ] Follow all AdSense guidelines

### Best Practices
- [ ] Test thoroughly before going live
- [ ] Monitor performance regularly
- [ ] Don't show excessive ads
- [ ] Respect user privacy
- [ ] Keep content quality high

### Troubleshooting
- [ ] If ads don't show: Check Publisher ID
- [ ] If ads show to all users: Check session_manager.is_guest
- [ ] If WebView errors: Check Flet version
- [ ] If import errors: Check __init__.py exists

---

## 📞 NEXT STEPS

1. **Immediate** (Next 5 minutes)
   - [ ] Read: `GOOGLE_ADS_SETUP.md` (detailed setup guide)
   - [ ] Or read: `QUICK_REFERENCE.md` (quick summary)

2. **Today** (Next few hours)
   - [ ] Create Google AdSense account (if needed)
   - [ ] Wait for approval if new account

3. **When Approved** (24-48 hours for new accounts)
   - [ ] Get Publisher ID
   - [ ] Create 3 ad units
   - [ ] Copy all Slot IDs

4. **Configuration** (30 minutes)
   - [ ] Update `google_ads_service.py`
   - [ ] Save and verify syntax

5. **Testing** (30 minutes)
   - [ ] Test guest user (ads should show)
   - [ ] Test authenticated user (no ads)
   - [ ] Verify all 3 screens

6. **Go Live** (When ready)
   - [ ] Deploy to production
   - [ ] Monitor AdSense dashboard
   - [ ] Track impressions and earnings

---

## 📚 DOCUMENTATION

For detailed information:

| Document | Purpose | Time |
|----------|---------|------|
| `QUICK_REFERENCE.md` | Quick overview | 5 min |
| `GOOGLE_ADS_SETUP.md` | Step-by-step setup | 20 min |
| `GOOGLE_ADS_IMPLEMENTATION.md` | How it works | 15 min |
| `GOOGLE_ADS_EXAMPLES.md` | Code examples | 20 min |
| `INSTALLATION_SUMMARY.md` | What was installed | 10 min |

---

## ✅ COMPLETION TRACKER

**Installation**: ✅ 100% COMPLETE

**Configuration**: ⏳ 0% - Ready for you to start

**Testing**: ⏳ 0% - Ready once configured

**Go-Live**: ⏳ 0% - Ready once tested

---

## 🎉 You're Ready!

All the infrastructure is in place. Just follow the configuration steps above and you'll have Google Ads working in your Video Merger App!

**Start with**: `GOOGLE_ADS_SETUP.md` for detailed instructions

---

**Last Updated**: December 6, 2025
**Status**: Ready for AdSense configuration
**Est. Time to Complete**: 1-2 days (waiting for AdSense approval)
