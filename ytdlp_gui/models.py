from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

class DownloadStatus(Enum):
    QUEUED = "queued"
    WAITING = "waiting"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class QualityPreset(Enum):
    MAXIMUM = "maximum"
    HIGH = "high"
    BALANCED = "balanced"
    AUDIO_ONLY = "audio"
    VIDEO_ONLY = "video_only"

class OutputFormat(Enum):
    MP4 = "mp4"
    MKV = "mkv"
    MP3 = "mp3"
    WEBM = "webm"
    OPUS = "opus"
    FLAC = "flac"
    WAV = "wav"

class AudioCodec(Enum):
    MP3 = "mp3"
    OPUS = "opus"
    FLAC = "flac"
    WAV = "wav"
    AAC = "aac"
    VORBIS = "vorbis"
    BEST = "best"

@dataclass
class DownloadTask:

    url: str
    output_dir: str
    quality: QualityPreset = QualityPreset.MAXIMUM
    format: OutputFormat = OutputFormat.MP4
    subtitles: bool = False
    subtitle_langs: str = "en,en-US"
    thumbnail: bool = True
    metadata: bool = True
    chapters: bool = True
    sponsorblock: bool = False
    cookies_path: str = ""
    proxy: str = ""
    speed_limit: int = 0
    playlist_mode: bool = False
    audio_codec: AudioCodec = AudioCodec.MP3
    audio_quality: int = 320

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: DownloadStatus = DownloadStatus.QUEUED
    title: str = "Pending…"
    progress: float = 0.0
    speed: float = 0.0
    eta: int = 0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    error: str = ""
    retries_used: int = 0
    started_at: float = 0.0
    completed_at: float = 0.0
    playlist_index: int = 0
    playlist_total: int = 0
    output_path: str = ""

@dataclass
class VideoInfo:
    title: str = "Unknown"
    duration: int = 0
    uploader: str = "Unknown"
    view_count: int = 0
    like_count: int = 0
    upload_date: str = ""
    description: str = ""
    thumbnail_url: str = ""
    is_playlist: bool = False
    playlist_count: int = 0
    available_resolutions: list[int] = field(default_factory=list)
    max_resolution: int = 0
    max_fps: int = 0
    has_hdr: bool = False
    filesize_approx: int = 0
    error: str = ""
