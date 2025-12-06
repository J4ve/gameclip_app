# Google Ads - Quick Reference Card

## 📍 WHERE WERE THINGS ADDED?

### New Service Files
```
src/app/services/
├── __init__.py                 ← New: Package initialization
├── google_ads_service.py       ← New: Core ad service  
└── ads_manager.py              ← New: Ad manager singleton
```

### Modified UI Screens
```
src/app/gui/
├── selection_screen.py         ← MODIFIED: + Rectangle ad (right)
├── arrangement_screen.py       ← MODIFIED: + Banner ad (top)
└── save_upload_screen.py       ← MODIFIED: + Banner ad (top)
```

### Documentation Files
```
Root directory:
├── GOOGLE_ADS_README.md        ← Overview & quick start
├── GOOGLE_ADS_SETUP.md         ← Step-by-step setup guide
├── GOOGLE_ADS_IMPLEMENTATION.md ← How it works
├── GOOGLE_ADS_EXAMPLES.md      ← Code examples
└── INSTALLATION_SUMMARY.md     ← This installation report
```

---

## ⚡ QUICK START (3 Steps)

### 1️⃣ Get Google Publisher ID
- Go: https://www.google.com/adsense/
- Find: `ca-pub-XXXXXXXXXXXXXXXX`
- Copy: This ID

### 2️⃣ Create Ad Units
- Dashboard → Ads → Ad Units
- Create 3 units, copy their Slot IDs:
  - Rectangle (300x250)
  - Banner (728x90)
  - Sidebar (300x600) [optional]

### 3️⃣ Update Config File
File: `src/app/services/google_ads_service.py`
```python
PUBLISHER_ID = "ca-pub-YOUR_ID"  # Line 15
AD_SLOTS = {                      # Lines 19-34
    "horizontal_banner": {
        "slot_id": "YOUR_SLOT_ID",
    },
    # ... other slots
}
```

---

## 💻 USAGE IN CODE

```python
# Import
from app.services.ads_manager import (
    should_show_ads,
    get_rectangle_ad,
    get_banner_ad,
)

# Use
if should_show_ads():
    ad = get_rectangle_ad()
    # Add to layout
```

---

## 🎯 AD PLACEMENTS

| Screen | Ad | Size | Position |
|--------|-----|------|----------|
| Selection | Rectangle | 300x250 | Right side |
| Arrangement | Banner | 728x90 | Top |
| Save/Upload | Banner | 728x90 | Top |

---

## 🧪 TEST IT

### Test 1: Guest User
```
Login: Click "continue without signing in"
Check: Ads appear in all 3 screens
```

### Test 2: Authenticated User
```
Login: Click "Sign in with Google"
Check: NO ads appear anywhere
```

---

## 📚 DOCUMENTATION MAP

| Need | Read |
|------|------|
| Overview | `GOOGLE_ADS_README.md` |
| Setup help | `GOOGLE_ADS_SETUP.md` |
| Code examples | `GOOGLE_ADS_EXAMPLES.md` |
| How it works | `GOOGLE_ADS_IMPLEMENTATION.md` |
| Installation | `INSTALLATION_SUMMARY.md` |

---

## ✅ WHAT'S INCLUDED

✓ Core service (google_ads_service.py)
✓ Manager singleton (ads_manager.py)
✓ 3 screens updated with ads
✓ 5 documentation files
✓ All syntax verified ✓ 
✓ All imports tested ✓

---

## ⚠️ IMPORTANT

- Ads show ONLY to guest users
- Authenticated users see NO ads
- Requires Google AdSense account
- Must update Publisher ID + Slot IDs
- WebView-based (safe, isolated)

---

## 🚨 TROUBLESHOOTING

### Ads not showing?
1. Check Publisher ID is correct
2. Verify user is guest (not authenticated)
3. Confirm Slot IDs are correct
4. Check `should_show_ads()` returns True

### Configuration issues?
1. Review lines 15-34 in `google_ads_service.py`
2. See `GOOGLE_ADS_SETUP.md` for details
3. Run import test to verify code works

### Need help?
1. Read `GOOGLE_ADS_SETUP.md` first
2. Check `GOOGLE_ADS_EXAMPLES.md` for code
3. Review `GOOGLE_ADS_IMPLEMENTATION.md` for details

---

## 📊 FILES SUMMARY

| File | Type | Status |
|------|------|--------|
| google_ads_service.py | Python | ✓ Created |
| ads_manager.py | Python | ✓ Created |
| __init__.py | Python | ✓ Created |
| selection_screen.py | Python | ✓ Modified |
| arrangement_screen.py | Python | ✓ Modified |
| save_upload_screen.py | Python | ✓ Modified |
| GOOGLE_ADS_README.md | Docs | ✓ Created |
| GOOGLE_ADS_SETUP.md | Docs | ✓ Created |
| GOOGLE_ADS_IMPLEMENTATION.md | Docs | ✓ Created |
| GOOGLE_ADS_EXAMPLES.md | Docs | ✓ Created |
| INSTALLATION_SUMMARY.md | Docs | ✓ Created |

---

## 🎓 CONCEPTS

### Guest-Only Monetization
- Ads only for guests (free users)
- No ads for authenticated users (premium)
- Automatic detection via session_manager

### WebView Integration
- HTML with AdSense script
- Base64 encoded
- Safe, isolated from main app
- Flet WebView renders

### Smart Placement
- Selection: Rectangle on right
- Arrangement: Banner at top
- Save/Upload: Banner at top

---

## 🚀 NEXT STEPS

1. Read: `GOOGLE_ADS_SETUP.md`
2. Create: AdSense account (if needed)
3. Get: Publisher ID + 3 Slot IDs
4. Update: `google_ads_service.py` lines 15-34
5. Test: Login as guest and check ads appear
6. Verify: Authenticated users see NO ads

---

## 🎉 STATUS

**Installation**: ✅ COMPLETE
**Configuration**: ⏳ PENDING (needs your AdSense credentials)
**Testing**: ⏳ READY (once configured)
**Deployment**: ⏳ READY (once tested)

---

*For complete details, see GOOGLE_ADS_README.md*
*For setup instructions, see GOOGLE_ADS_SETUP.md*
*For code examples, see GOOGLE_ADS_EXAMPLES.md*
