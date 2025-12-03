# 🎮 Video Merger and Uploader

An open-source desktop tool for streamers and video editors to automatically upload merged clips and VODs to YouTube — no manual renaming, no manual editing, no repetitive settings, and optional automatic highlight compilations.

> **📋 Project Foundation**: This application is based on the [Long-Term Software Requirements Specification (LTSRS)](./Group7_LTSRS.pdf) developed by our team. The SRS document outlines the complete system requirements, functional specifications, and design constraints that guide the development of this project.

---

## 🛠️ Tech Stack
**Core**
- Python 3.x
- YouTube Data API v3 (video upload, metadata)
- FFmpeg (video merging, thumbnail extraction)

**Frontend (GUI)**
- Flet 0.28.3 (Python UI framework)

**Key Dependencies**
- `flet` - Cross-platform GUI framework
- `ffmpeg-python` - Python bindings for FFmpeg
- `requests` - HTTP library for API calls
- `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client` - Google API client libraries for YouTube upload

**Configuration & Data**
- JSON/YAML (templates, profiles)
- CSV (clip manifests)

**Testing & DevOps**
- pytest (unit testing)
- GitHub + GitHub Actions (version control, CI/CD)
- PyInstaller / Flet pack (packaging for distribution)

**Optional Future Add-ons**
- SQLite (local database for upload history)
- Docker (portable dev environment)
- Cloud storage (Google Drive / AWS S3 backups)

---

## 🔄 SDLC Model
The project follows an **Agile / Iterative-Incremental model**:
- Work is divided into milestones (phases).
- Each milestone delivers a working feature (Setup → GUI → Compilation → Uploader → Distribution).
- Feedback-driven improvement.

### Requirements Engineering
The project is based on our **Software Requirements Specification (SRS) v1.0** which defines:
- **Functional Requirements**: User authentication (OAuth 2.0), video selection/arrangement, FFmpeg-based merging, YouTube upload with metadata, progress tracking, and error handling
- **Non-Functional Requirements**: Performance targets (<5 min for 10 HD clips), usability (3-attempt learning curve), security (encrypted token storage), reliability (auto-resume uploads), and maintainability (modular architecture)
- **System Constraints**: Windows 10+, Python with Flet framework, FFmpeg integration, YouTube Data API v3 compliance

For detailed specifications, see [Group7_LTSRS.pdf](./Group7_LTSRS.pdf).

---

## 📍 Workflow
1. **Repo Setup**: `src/` for code, `tests/`, configs, README, GitHub Actions.
2. **Branching**:
   - `main`: stable
   - `dev`: integration
   - `feature/*`: new features
3. **Milestones → Issues → Commits**:
   - Milestones = phases (Uploader, Compilation, GUI, etc.).
   - Issues = tasks grouped under milestones.
   - Commits = code changes tied to issues.

---

## 🗂️ Roadmap
### Milestone 1: Project Setup & Foundation ✅
- [x] Initialize repository structure
- [x] Set up virtual environment
- [x] Install core dependencies (flet, ffmpeg-python, pillow, requests, tqdm)
- [x] Create README documentation
- [x] Set up GitHub repository with proper branching
- [x] Create initial project structure (src/, tests/, configs/)

### Milestone 2: GUI (Flet) ✅
- [x] GUI skeleton (tabs: Upload, Compilation, Config)
- ~~[ ] Drag & drop folder support~~
- [x] Select videos through clicking
- [x] File browser integration

### Milestone 3: Compilation Feature ✅
- [x] Video selection interface
- [x] FFmpeg integration for merging clips
- [x] Preview functionality
- [x] Output format configuration

### Milestone 4: Core Uploader
- [ ] YouTube API auth setup (OAuth 2.0)
- [ ] Single video upload with requests
- [ ] Upload queue + progress bars
- [ ] JSON/YAML config for title/description/tags
- [ ] Upload compiled video with template
- [ ] Metadata template system

### Milestone 5: Access Control System
- [ ] Firebase project setup
- [ ] Enable Authentication & Firestore
- [ ] Implement Login / Signup / Logout
- [ ] Load user roles on login
- [ ] Define roles: guest, user, premium, admin
- [ ] Create Firestore user documents
- [ ] Apply custom role claims
- [ ] Role-based UI restrictions
- [ ] Guest/User: watermark + merge limits
- [ ] Premium: full access, no watermark
- [ ] Admin dashboard (view users)
- [ ] Admin role editing (promote/demote)
- [ ] Admin ban/unban users
- [ ] Firestore security rules by role
- [ ] Comprehensive role testing & bypass attempts

### Milestone 6: Scheduling + Polish
- [ ] Support `publishAt` scheduling
- [ ] Thumbnail generation with Pillow
- [ ] Upload progress tracking
- [ ] Logs + error retries
- [ ] CSV manifest support

### Milestone 7: Distribution
- [ ] Package with Flet pack / PyInstaller
- [ ] GitHub Actions CI/CD pipeline
- [ ] Windows executable build
- [ ] Cross-platform testing
- [ ] Release v1.0

---

## 📦 Installation & Setup

### API Credentials (YouTube)

You must provide your own YouTube API OAuth credentials for uploads. The file `src/uploader/client_secret.json` **should NOT be committed to Git or shared publicly.**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select your existing one)
3. Enable the YouTube Data API v3
4. Go to "APIs & Services" → "Credentials"
5. Create OAuth 2.0 Client ID (Desktop app)
6. Download the `client_secret.json` file
7. Place it in `src/uploader/client_secret.json`
8. **Do not commit this file to Git!**
9. If you ever accidentally commit it, delete it from Git history and regenerate credentials in Google Cloud Console.

### Clone the repository
```bash
git clone https://github.com/J4ve/videomerger_app.git
cd videomerger_app
```

### Set up virtual environment
```bash
# Create virtual environment
python -m venv env

# Activate (Windows PowerShell)
.\env\Scripts\Activate.ps1

# Activate (Windows cmd)
.\env\Scripts\activate.bat

# Activate (Linux/macOS)
source env/bin/activate
```

### Install dependencies

**Option 1: Install directly (recommended for development)**
```bash
pip install flet ffmpeg-python pillow requests tqdm pytest google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

**Option 2: Use requirements file**
```bash
pip install -r requirements.txt
```

**Note**: Ensure FFmpeg is installed on your system for video processing:
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) or use `winget install FFmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (Fedora/CentOS)

---

## 🚀 Run the App

**Important**: Navigate to the `src/` directory before running the app:
```bash
cd src
```

### Standard Python Environment

Run as a desktop app:
```bash
flet run
```

Run as a web app:
```bash
flet run --web
```

### Using uv

Run as a desktop app:
```bash
uv run flet run
```

Run as a web app:
```bash
uv run flet run --web
```

### Using Poetry

Install dependencies:
```bash
poetry install
```

Run as a desktop app:
```bash
poetry run flet run
```

Run as a web app:
```bash
poetry run flet run --web
```

For more details on running the app, refer to the [Getting Started Guide](https://flet.dev/docs/getting-started/).

---

## 📦 Build the App

### Windows
```bash
flet build windows -v
```
For more details, see the [Windows Packaging Guide](https://flet.dev/docs/publish/windows/).

### Linux
```bash
flet build linux -v
```
For more details, see the [Linux Packaging Guide](https://flet.dev/docs/publish/linux/).

### macOS
```bash
flet build macos -v
```
For more details, see the [macOS Packaging Guide](https://flet.dev/docs/publish/macos/).

### Android
```bash
flet build apk -v
```
For more details on building and signing `.apk` or `.aab`, see the [Android Packaging Guide](https://flet.dev/docs/publish/android/).

### iOS
```bash
flet build ipa -v
```
For more details on building and signing `.ipa`, see the [iOS Packaging Guide](https://flet.dev/docs/publish/ios/).

---

## 📚 Documentation
- **[Software Requirements Specification (SRS)](./Group7_LTSRS.pdf)** - Complete system requirements and specifications (v1.0, October 2025)
- **[Flet Documentation](https://flet.dev/docs/)** - GUI framework reference
- **[YouTube Data API v3](https://developers.google.com/youtube/v3)** - Upload API documentation
- **[FFmpeg Documentation](https://ffmpeg.org/documentation.html)** - Video processing reference

---

## 📜 License
MIT

---

## 👥 Contributors
- J4ve
- GeraldUnderdog
- mprestado
