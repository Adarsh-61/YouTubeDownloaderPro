<p align="center">
  <h1 align="center">YouTube Downloader Pro v3.0</h1>
  <p align="center">
    A modern, production-grade YouTube downloader with a polished GUI,<br>
    multi-strategy retry engine, and 8K → 720p quality cascade.
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
    <img src="https://img.shields.io/badge/version-3.0.0-orange" alt="Version 3.0.0">
    <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Cross-platform">
  </p>
</p>

---

## Table of Contents

- [Overview](#overview)
- [What Changed from v1 → v3](#what-changed-from-v1--v3)
- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Usage Guide](#usage-guide)
- [Quality Presets](#quality-presets)
- [Multi-Strategy Retry Engine](#multi-strategy-retry-engine)
- [Configuration Reference](#configuration-reference)
- [Architecture](#architecture)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Overview

**YouTube Downloader Pro** is a desktop application for downloading YouTube videos, playlists, and audio. It wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) with an intelligent multi-strategy retry engine that automatically recovers from transient HTTP errors (403, 429, 503, timeouts) by cycling through up to **4 video** and **3 audio** fallback format strategies — ensuring downloads complete reliably even on unstable or throttled networks.

The application provides a clean four-tab interface (**Download · Queue · History · Settings**) built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter), offering full control over quality, format, subtitles, SponsorBlock, proxy, cookies, and 25+ other preferences. All settings persist across sessions in a JSON configuration file.

### Key Highlights

- **Resilient downloads** — subtitle/thumbnail failures are gracefully skipped; the video always downloads
- **Smart error classification** — retryable errors (403, 429, 503) trigger automatic fallback; non-retryable errors (private, deleted) stop immediately
- **5 quality presets** — Maximum (8K→720p with HDR/high-FPS preference), High (1080p), Balanced (720p), Audio Only (6 codecs), Video Only (no audio)
- **Concurrent downloads** — semaphore-based parallelism (1–5 simultaneous) with per-video fragment parallelism (1–8)
- **Cross-platform** — Windows, macOS, and Linux with platform-native file manager integration

---

## What Changed from v1 → v3

| Area | v1.0 | v2.0 | **v3.0 (current)** |
|------|------|------|---------------------|
| **Architecture** | Single 600-line file | 11-module package | 11-module package with dataclasses, enums, type hints |
| **UI Framework** | tkinter | CustomTkinter | CustomTkinter with segmented buttons, tabbed interface, dark/light/system themes |
| **Download Engine** | Basic yt-dlp call | Queue with concurrency | Multi-strategy retry with 7 fallback strategies and graceful degradation |
| **Quality** | 3 presets | 3 presets | 5 presets (Maximum 8K→720p, High, Balanced, Audio Only, Video Only) |
| **Audio** | MP3 only | MP3 only | MP3, OPUS, FLAC, WAV, AAC, Vorbis — configurable bitrate |
| **Network** | None | None | Proxy (SOCKS5/HTTP), speed limiting, cookies, configurable timeouts |
| **Resilience** | No retry | Basic retry | 4+3 fallback strategies, smart error classification, graceful subtitle/thumbnail skip |
| **Features** | Download only | + Queue, settings | + SponsorBlock, subtitles, chapters, thumbnails, metadata, playlist mode, video analysis |
| **History** | None | JSON file | Persistent JSON with search, re-download, copy URL, export |

### How v3.0 Became Significantly Better

1. **Downloads no longer fail on non-critical errors.** In v2.0, a single subtitle HTTP 429 error would kill the entire download. v3.0 sets `ignoreerrors: True` with a custom yt-dlp logger that captures and classifies errors — subtitles/thumbnails fail gracefully while truly fatal errors (video unavailable, private, deleted) are still detected and reported.

2. **Fallback strategies preserve quality preferences.** When the engine retries with a simpler format string, v3.0 still applies the active quality preset's `format_sort` and codec preferences, so fallback downloads maintain resolution and codec quality rather than falling back to arbitrary formats.

3. **Partial playlist success is recognized.** A playlist of 100 videos where 2 are unavailable now reports success after downloading 98 — instead of failing the entire batch.

4. **The engine is fully observable.** All yt-dlp warnings and errors are forwarded to the app's log box, giving users real-time visibility into what's happening during a download.

5. **The UI is production-quality.** Theme switching (dark/light/system) with instant preview, cookies file browser, concurrent fragment control, and 25+ persistent settings.

---

## Features

| Category | Details |
|----------|---------|
| **Modern GUI** | Dark / light / system themes, tabbed interface, segmented quality selector |
| **Quality Cascade** | 8K → 4K → 2K → 1080p → 720p → best available, with HDR and high-FPS preference |
| **5 Quality Presets** | Maximum (8K→720p), High (1080p), Balanced (720p), Audio Only, Video Only |
| **Multi-Strategy Retry** | 4 video + 3 audio fallback strategies on HTTP 403/429/503/timeout/reset |
| **Graceful Degradation** | Subtitle/thumbnail download failures are silently skipped — the video always downloads |
| **Audio Codecs** | MP3, OPUS, FLAC, WAV, AAC, Vorbis — configurable bitrate (128–320 kbps) |
| **Download Queue** | Visual queue with per-task progress, retry, cancel, and open-folder buttons |
| **Persistent History** | Searchable history (up to 1,000 entries) with re-download, copy URL, and JSON export |
| **SponsorBlock** | Automatic sponsor/self-promo/interaction segment removal |
| **Subtitles** | Multi-language subtitle download and embedding (comma-separated ISO codes) |
| **Output Formats** | MP4, MKV, WebM, MP3, OPUS, FLAC, WAV — with thumbnail, metadata, and chapter embedding |
| **Network** | SOCKS5/HTTP proxy, speed limiting, configurable socket timeout, cookies file browser |
| **Performance** | Concurrent fragment downloads (1–8), semaphore-based concurrency (1–5), 10 MB HTTP chunks |
| **Video Analysis** | Pre-download metadata: title, duration, resolution, FPS, HDR, view count, file size estimate |
| **Playlist Support** | Full playlist download with numbered output (`001 - Title.ext`), automatic URL detection |
| **URL Validation** | 15+ YouTube URL patterns: watch, shorts, live, embed, music, channel, handle, clips, playlists |
| **Disk Safety** | Free space checking before download with configurable safety margin |
| **Cross-Platform** | Windows, macOS, Linux — platform-native file manager integration |
| **25+ Settings** | All preferences saved to `~/.ytdlp_gui/settings.json` with one-click Reset to Defaults |

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.10 | 3.12+ |
| **OS** | Windows 10, macOS 12, Ubuntu 20.04 | Latest stable release |
| **FFmpeg** | 5.0 | 7.0+ (for AV1/HDR support) |
| **RAM** | 256 MB | 512 MB+ |
| **Disk** | 100 MB (application) | 10+ GB free (for video storage) |
| **Network** | Any internet connection | Broadband recommended |

### Python Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | ≥ 2024.1.0 | YouTube extraction, downloading, and post-processing |
| [customtkinter](https://github.com/TomSchimansky/CustomTkinter) | ≥ 5.2.0 | Modern cross-platform GUI framework |

FFmpeg is a **system** dependency (not a Python package) required for merging video/audio streams, transcoding, and embedding thumbnails/subtitles.

---

## Installation

### Step 1 — Install Python 3.10+

Download from [python.org](https://www.python.org/downloads/).
On Windows, check **"Add Python to PATH"** during installation.

```bash
python --version   # verify: should print 3.10 or newer
```

### Step 2 — Get the Source Code

**Option A — Clone with Git:**
```bash
git clone https://github.com/AdarshPandey-dev/YouTubeDownloaderPro.git
cd YouTubeDownloaderPro
```

**Option B — Download ZIP:**
Download from the repository page and extract to a folder.

### Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs `yt-dlp` and `customtkinter`. All other dependencies are part of the Python standard library.

### Step 4 — Install FFmpeg

FFmpeg is required for merging video and audio streams, audio extraction, thumbnail/subtitle embedding, and format remuxing.

<details>
<summary><strong>Windows</strong></summary>

1. Download from [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/) (choose the **full** build)
2. Extract the archive
3. Add the `bin` folder to your system PATH:
   - **Settings → System → About → Advanced system settings → Environment Variables**
   - Under **System variables**, select `Path` → **Edit** → **New**
   - Paste the full path to the `bin` folder (e.g. `C:\ffmpeg\bin`)
4. Open a new terminal and verify:
   ```bash
   ffmpeg -version
   ```

</details>

<details>
<summary><strong>macOS</strong></summary>

```bash
brew install ffmpeg
```

</details>

<details>
<summary><strong>Linux (Debian/Ubuntu)</strong></summary>

```bash
sudo apt update && sudo apt install ffmpeg
```

</details>

<details>
<summary><strong>Linux (Fedora)</strong></summary>

```bash
sudo dnf install ffmpeg
```

</details>

### Step 5 — Launch

```bash
python youtube_downloader.py
```

Or run as a Python module:

```bash
python -m ytdlp_gui
```

The status bar at the bottom of the window confirms FFmpeg and yt-dlp detection.

---

## Usage Guide

### Downloading a Video

1. **Paste a URL** — Copy a YouTube URL and click **Paste** (or type/paste directly and press `Enter`)
2. **Select quality** — Choose from the segmented preset bar: Maximum, High, Balanced, Audio Only, or Video Only
3. **Choose format** — Pick the output container (MP4, MKV, WebM for video; MP3, OPUS, FLAC, WAV for audio)
4. **Toggle options** — Enable or disable Subtitles, Thumbnail, Metadata, Chapters, SponsorBlock, Playlist mode
5. **Set output directory** — Browse or type the destination folder
6. **Click Start Download** — Progress is shown in real time (speed, ETA, bytes)

### Analyzing a Video Before Downloading

Click **Analyze** to preview metadata without starting a download:

- Title, duration, uploader, view count
- Maximum available resolution and FPS
- HDR availability
- Estimated file size

### Managing the Download Queue

Switch to the **Queue** tab to see all active, queued, and completed downloads:

- **Cancel** (✕) — Stop a running download
- **Retry** (↻) — Re-submit a failed download with the same settings
- **Open Folder** (📂) — Open the output directory in your file manager
- **Clear Done** — Remove all completed/failed/canceled entries from the list

### Browsing Download History

The **History** tab stores up to 1,000 past downloads across sessions:

- **Search** — Filter by title or URL (250ms debounce for smooth typing)
- **Re-download** (↻) — One click to populate the Download tab with the URL
- **Copy URL** (📋) — Copy to clipboard
- **Export** — Save the full history as a JSON file

### Downloading a Playlist

1. Paste a playlist URL — the app auto-detects URLs containing `list=`
2. **Playlist mode** is automatically enabled (or toggle manually)
3. Files are saved as `001 - Title.ext`, `002 - Title.ext`, etc., inside a folder named after the playlist

### Using Cookies for Authenticated Downloads

Some videos require authentication (age-restricted, members-only):

1. Install a browser extension like "Get cookies.txt LOCALLY"
2. Export your YouTube cookies and save as `cookies.txt`
3. In the app, go to **Settings → Cookies file → Browse** and select the file

---

## Quality Presets

| Preset | Resolution | Container | Codec Preference | Notes |
|--------|-----------|-----------|------------------|-------|
| **Maximum** | 8K → 4K → 2K → 1080p → 720p | MKV | AV1 → VP9.2 → VP9 → HEVC → H.264 | Best available quality, HDR and high-FPS preferred, `format_sort_force` enabled |
| **High** | ≤ 1080p | MP4 | H.264 → HEVC | Wide device compatibility |
| **Balanced** | ≤ 720p | MP4 | Auto | Smallest reasonable file size |
| **Audio Only** | — | MP3/OPUS/FLAC/WAV/AAC | Configurable | Codec and bitrate selectable (128–320 kbps) |
| **Video Only** | 8K → 720p | MP4 | AV1 → VP9 → HEVC → H.264 | Video stream without audio, useful for editing |

---

## Multi-Strategy Retry Engine

When a download fails with a retryable error, the engine cycles through fallback format strategies instead of giving up. Non-retryable errors immediately stop the fallback chain. Fallback strategies inherit the active preset's `format_sort` and codec preferences, so retried downloads maintain quality.

### Error Classification

| Type | Examples | Engine Behavior |
|------|----------|-----------------|
| **Retryable** | HTTP 403 (CDN block), 429 (rate limit), 503 (server busy), timeout, connection reset, incomplete data | Tries next fallback strategy automatically |
| **Non-retryable** | Video unavailable, private, deleted, copyright takedown | Stops immediately, reports the error |
| **Non-critical** | Subtitle 429, thumbnail download failure | Silently skipped — video still downloads |

### Video Fallback Strategies (4 levels)

| # | Strategy | Format String | Why It Helps |
|---|----------|---------------|--------------|
| 1 | Resolution cascade | `bv*[height>=4320]+ba/…/bv*+ba/best` | Explicit resolution preference with all heights |
| 2 | Simple best | `bestvideo+bestaudio/best` | Some extractors handle simple expressions better |
| 3 | Progressive only | `best[height>=1080]/best[height>=720]/best` | Avoids merge step, bypasses some CDN 403 errors |
| 4 | Last resort | `best` | Accepts any available format |

### Audio Fallback Strategies (3 levels)

| # | Strategy | Format String |
|---|----------|---------------|
| 1 | Codec preference | `bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best` |
| 2 | Generic best | `bestaudio/best` |
| 3 | Last resort | `best` |

---

## Configuration Reference

All settings persist in `~/.ytdlp_gui/settings.json` and are editable from the **Settings** tab.

### Appearance

| Setting | Default | Description |
|---------|---------|-------------|
| Theme | `light` | `dark`, `light`, or `system` (follows OS) — instant preview on save |
| Window size | 1100 × 820 | Automatically saved on exit |

### Quality & Format

| Setting | Default | Description |
|---------|---------|-------------|
| Quality preset | Maximum | Default quality for new downloads |
| Output format | MP4 | Default container format |
| Audio codec | MP3 | Codec for audio-only extraction |
| Audio bitrate | 320 kbps | Bitrate for lossy audio codecs (128–320) |

### Post-Processing

| Setting | Default | Description |
|---------|---------|-------------|
| Subtitles | Off | Download and embed subtitles |
| Subtitle languages | `en,en-US` | Comma-separated ISO language codes |
| Thumbnail | On | Embed video thumbnail |
| Metadata | On | Embed title, artist, date metadata |
| Chapters | On | Embed chapter markers |
| SponsorBlock | Off | Remove sponsor/self-promo/interaction segments |

### Network

| Setting | Default | Description |
|---------|---------|-------------|
| Proxy | None | SOCKS5 or HTTP proxy URL (e.g. `socks5://127.0.0.1:1080`) |
| Speed limit | 0 (unlimited) | Maximum download speed in bytes/sec |
| Socket timeout | 30s | Connection timeout |
| Cookies file | None | Path to `cookies.txt` for authenticated downloads |

### Performance

| Setting | Default | Description |
|---------|---------|-------------|
| Concurrent downloads | 2 | Simultaneous downloads (1–5) |
| Concurrent fragments | 4 | Parallel fragment downloads per video (1–8) |
| Max retries | 10 | Download retry attempts |
| Fragment retries | 10 | Per-fragment retry count |
| HTTP chunk size | 10 MB | Download chunk size |
| Buffer size | 128 KB | Stream buffer size |

### File Handling

| Setting | Default | Description |
|---------|---------|-------------|
| Windows-safe filenames | On | Replace characters invalid on Windows |
| Restrict filenames | Off | Limit filenames to ASCII characters only |
| Overwrite existing | Off | Whether to overwrite existing files |

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    App  (CTk window)                     │
│   Main controller: tab wiring, event routing, lifecycle  │
├──────────┬──────────┬──────────────┬─────────────────────┤
│ Download │  Queue   │   History    │      Settings       │
│   Tab    │   Tab    │     Tab      │        Tab          │
│  URL,    │  active, │  search,     │  25+ options,       │
│  quality,│  retry,  │  re-download,│  theme, proxy,      │
│  format, │  cancel, │  copy URL,   │  cookies, reset,    │
│  options │  folder  │  export      │  update yt-dlp      │
├──────────┴──────────┴──────────────┴─────────────────────┤
│                   DownloadEngine                         │
│   Semaphore concurrency · Multi-strategy retry           │
│   Progress hooks · Post-processor hooks                  │
│   _YtdlpLogger (error capture) · Thread-safe callbacks   │
├──────────────────────────────────────────────────────────┤
│                 yt-dlp  +  FFmpeg                        │
│   Extraction · Download · Merge · Transcode              │
└──────────────────────────────────────────────────────────┘
```

### Project Structure

```
YouTubeDownloaderPro/
├── youtube_downloader.py        # Entry point — dependency check, then launch
├── pyproject.toml               # PEP 621 packaging metadata
├── requirements.txt             # pip dependencies
├── README.md                    # This file
├── LICENSE                      # MIT License
└── ytdlp_gui/                   # Main package (11 modules)
    ├── __init__.py              # Package version + public API exports
    ├── __main__.py              # python -m ytdlp_gui support
    ├── models.py                # Dataclasses: DownloadTask, VideoInfo
    │                            # Enums: DownloadStatus, QualityPreset,
    │                            #        OutputFormat, AudioCodec
    ├── config.py                # SettingsManager, AppSettings (dataclass),
    │                            # load_history(), save_history()
    ├── utils.py                 # URL validation (15+ patterns), formatting,
    │                            # disk checks, FFmpeg detection, open_folder()
    ├── engine.py                # DownloadEngine — core download logic:
    │                            #   QualityPresets, _YtdlpLogger,
    │                            #   fallback strategies, progress hooks
    ├── app.py                   # App (CTk) — window shell, tab wiring,
    │                            #   engine callbacks, lifecycle management
    ├── download_tab.py          # Download configuration UI
    ├── queue_tab.py             # Queue management UI
    ├── history_tab.py           # History viewer UI
    └── settings_tab.py          # Settings UI — 25+ preferences
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Thread-safe callbacks via `CTk.after(0, ...)`** | All engine callbacks marshal updates to the main thread, preventing Tcl/Tk threading violations |
| **`threading.Semaphore` for concurrency** | Lightweight concurrency control without thread pool overhead; easily configurable (1–5) |
| **`threading.Event` for cancellation** | Each task gets an Event; the progress hook checks it and raises `DownloadError` to cleanly abort yt-dlp |
| **`ignoreerrors: True` + `_YtdlpLogger`** | Non-critical errors (subtitles, thumbnails) are silently skipped while fatal errors (private, deleted) are still detected and reported |
| **Preset applied before format override** | Fallback format strategies inherit `format_sort` and codec preferences from the active quality preset |
| **Partial success detection** | Playlist downloads where some items fail are treated as successful if at least one file was saved |
| **Debounced history search (250ms)** | Avoids recreating hundreds of widgets on every keystroke |
| **Python dataclasses for models** | Clean, typed data structures with no external dependency |

---

## Production Deployment

### Running from Source

```bash
python youtube_downloader.py
```

### Running as a Module

```bash
python -m ytdlp_gui
```

### Installing as a Package

```bash
pip install -e .
ytdlp-gui
```

### Building a Standalone Executable

Use [PyInstaller](https://pyinstaller.org/) to create a distributable binary:

```bash
pip install pyinstaller

# Windows
pyinstaller --onefile --windowed --name "YouTubeDownloaderPro" youtube_downloader.py

# macOS / Linux
pyinstaller --onefile --windowed --name "YouTubeDownloaderPro" youtube_downloader.py
```

The executable is created in `dist/`. Add `--icon=icon.ico` (Windows) or `--icon=icon.icns` (macOS) for a custom icon.

### Building a Distribution Package

```bash
pip install build
python -m build
```

Creates wheel (`.whl`) and source distribution (`.tar.gz`) in `dist/` for upload to PyPI or private registries.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **FFmpeg not found** | Install FFmpeg and add its `bin` directory to your system PATH. Restart the application. |
| **Subtitle download fails (HTTP 429)** | The video still downloads — subtitles are gracefully skipped. Try again later, or reduce concurrent requests. |
| **HTTP 403 errors** | The engine retries with up to 4 fallback strategies. If all fail, try a fresh `cookies.txt` from your browser. |
| **HTTP 429 (rate limited)** | Reduce concurrent downloads and fragments in Settings. The engine retries automatically. |
| **"Video unavailable"** | The video is private, deleted, or geo-blocked. Try a VPN/proxy. This is a non-retryable error. |
| **Slow downloads** | Increase concurrent fragments (Settings → Performance). Check your network connection. |
| **No subtitles found** | Not all videos have subtitles. Add `auto` to subtitle languages for auto-generated ones. |
| **Audio not extracted** | Select the **Audio Only** quality preset and choose your codec (MP3, FLAC, etc.). |
| **Age-restricted video** | Export browser cookies and set the path in Settings → Cookies file. |
| **yt-dlp out of date** | Click **Update yt-dlp** in Settings, or run `pip install -U yt-dlp`. |
| **App won't start** | Verify Python 3.10+: `python --version`. Reinstall deps: `pip install -r requirements.txt`. |
| **Settings corrupted** | Delete `~/.ytdlp_gui/settings.json` — the app recreates defaults on next launch. |
| **Download stuck at 0%** | Check internet connection. If using a proxy, verify reachability. Try concurrent downloads = 1. |
| **Merged file is corrupt** | Update FFmpeg to the latest version. Ensure enough disk space for temporary files. |
| **yt-dlp JS runtime warning** | Install [Deno](https://deno.com/) for full YouTube extraction support, or ignore — the fallback API works. |

---

## Roadmap

Planned features for future releases:

- [ ] Batch URL import from text file
- [ ] Download scheduler (time-based queuing)
- [ ] Bandwidth usage statistics and graphs
- [ ] Custom yt-dlp argument passthrough
- [ ] Drag-and-drop URL support
- [ ] System tray minimization with completion notifications
- [ ] Auto-update check for new application versions
- [ ] Export queue as shareable configuration
- [ ] Format preview with file size estimation before download
- [ ] Multi-language UI localization

---

## Disclaimer

This tool is intended for **personal, educational, and lawful purposes only**. Users are responsible for complying with YouTube's Terms of Service, applicable copyright laws, and any other relevant regulations. The authors do not endorse or encourage the unauthorized downloading of copyrighted content.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for the full text.

Copyright © 2026 Adarsh Pandey
