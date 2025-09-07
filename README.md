# 🎮 GameClip YouTube Uploader

An open-source desktop tool for streamers and gamers to automatically upload bulk clips and VODs to YouTube — no manual renaming, no repetitive settings, and optional automatic highlight compilations.

---

## ✨ Features (Planned)
- **Bulk Upload**: Upload multiple clips at once with template-based titles, descriptions, and tags.
- **Config Profiles**: Save game-specific settings (tags, titles, playlists).
- **Manifest Support**: Use CSV/JSON files to define metadata, publish dates, and highlight flags.
- **Compilation Mode**: Automatically merge selected clips into a single highlight video using FFmpeg.
- **Thumbnail Automation**: Generate thumbnails from video frames if none are provided.
- **Scheduling**: Spread uploads over time using YouTube’s `publishAt` scheduling.
- **GUI (Flet)**: Drag & drop interface, upload queue visualization, and progress bars.

---

## 🛠️ Tech Stack
**Core**
- Python
- YouTube Data API v3 (video upload, metadata)
- FFmpeg (video merging, thumbnail extraction)

**Frontend (GUI)**
- Flet (Python UI framework)

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
- Each milestone delivers a working feature (Uploader → Compilation → GUI).
- Feedback-driven improvement.

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
### Milestone 1: Core Uploader (MVP)
- [ ] YouTube API auth setup
- [ ] Single video upload
- [ ] Bulk folder upload
- [ ] JSON config for title/description

### Milestone 2: Compilation Feature
- [ ] Select videos for compilation
- [ ] Merge clips with FFmpeg
- [ ] Upload compilation with template

### Milestone 3: GUI (Flet)
- [ ] GUI skeleton (tabs: Upload, Compilation, Config)
- [ ] Drag & drop folder support
- [ ] Upload queue + progress bars

### Milestone 4: Scheduling + Polish
- [ ] Support `publishAt` scheduling
- [ ] Thumbnail generation
- [ ] Logs + error retries

### Milestone 5: Distribution
- [ ] Package with Flet pack / PyInstaller
- [ ] GitHub Actions builds for Windows/macOS
- [ ] Release v1.0

---

## 📦 Installation (Placeholder)
```bash
# Clone repo
git clone https://github.com/yourusername/gameclip-uploader.git
cd gameclip-uploader

# Install dependencies
pip install -r requirements.txt

# Run GUI
flet run src/gui/app.py
```

---

## 🏆 Differentiators
- Gamer/streamer focus (profiles per game).
- Hybrid workflow: individual clip uploads + compilations.
- Automation-first (zero manual renaming/settings).
- Easy-to-use desktop GUI with drag & drop.

---

## 📜 License
MIT

---

## 👥 Contributors
- Project Lead: J4ve
- Open to contributions via PRs & issues.

