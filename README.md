# YouTube Downloader Pro (Enhanced Version)

A modern, GUI-based YouTube downloader rebuilt for stability, clarity, and advanced feature support. Built with Python, yt-dlp, and FFmpeg.

## ✅ Features
- Auto-detects single videos vs playlists
- Best available quality (tries 8K → 4K → 1440p → 1080p → fallback)
- Audio-only extraction (MP3 320 kbps)
- Thumbnail, metadata, and chapter embedding
- Optional English (and auto) subtitles
- Real-time progress (percent, speed, ETA)
- Cancel support (pause/resume planned)
- Download history export (JSON)
- Thread-safe tkinter UI
- Uses yt-dlp + FFmpeg under the hood

## 🛠 Requirements
- Python 3.10 or newer
- yt-dlp (latest)
- FFmpeg (for merging, audio extraction, thumbnails, subtitles)
- Works on Windows / macOS / Linux (tkinter GUI)

## 📥 FFmpeg Installation

### Windows (quick method)
1. Download a full build:  
   https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z  
2. Extract the archive (7-Zip / WinRAR).  
3. Open the `bin` subfolder (contains `ffmpeg.exe`).  
4. Copy the path (e.g., `C:\Tools\ffmpeg\bin`).  
5. Open Start → "Edit the system environment variables".  
6. Environment Variables → Path → Edit → New → paste path → OK.  
7. Verify:  
   ```powershell
   ffmpeg -version
   ```

### macOS
```bash
brew install ffmpeg
ffmpeg -version
```

### Linux (Debian / Ubuntu)
```bash
sudo apt update
sudo apt install ffmpeg
ffmpeg -version
```

More builds: https://ffmpeg.org/download.html

## 📦 First-Time Install
```powershell
pip install --upgrade yt-dlp
```

(Optional virtual environment):
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip yt-dlp
```

## ▶️ Run
```powershell
python youtube_downloader.py
```

## 🎚 Quality Modes
- **Maximum**: 8K → 4K → 1440p → 1080p → best available
- **Balanced**: Up to 1080p
- **Audio Only**: MP3 (320 kbps)

## 📂 Output
Default directory: `~/Downloads/YouTube`  
Playlists are placed in a folder named after the playlist title.

## 🔄 Update yt-dlp
**In-app**: Tools → Update yt-dlp  
**Or manually**:
```powershell
pip install --upgrade yt-dlp
```

## 🧪 Quick Test
```powershell
python youtube_downloader.py
# Paste a YouTube URL
# (Optional) Click Analyze
# Select quality / format → Start Download
```

## 🛠 Troubleshooting
| Problem | Fix |
|---------|-----|
| FFmpeg not found | Add its `bin` directory to PATH |
| No subtitles | Not all videos provide them |
| Slow speed | Check network / disable VPN / retry later |
| MP3 not created | Choose Audio Only or set Format = MP3 |

## 🔐 Disclaimer
Use this tool only for personal, educational, and lawful purposes. Respect YouTube's Terms of Service and all copyright laws.

## 🚀 Roadmap
- Pause / resume
- Queue UI
- Dark mode
- Custom naming templates

Feedback, issues, and improvements are welcome. Enjoy!
