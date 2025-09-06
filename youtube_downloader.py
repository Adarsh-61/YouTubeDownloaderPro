import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import yt_dlp
import threading
import queue
import json
import time
from datetime import datetime
from pathlib import Path
import shutil
import re
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class AdvancedLogger:
    """Thread-safe logger with color coding and level filtering"""
    def __init__(self, text_widget, status_bar=None):
        self.text_widget = text_widget
        self.status_bar = status_bar
        self.message_queue = queue.Queue()
        self.setup_tags()
        self.start_update_thread()
        
    def setup_tags(self):
        """Configure text tags for colored output"""
        self.text_widget.tag_config("DEBUG", foreground="gray")
        self.text_widget.tag_config("INFO", foreground="black")
        self.text_widget.tag_config("SUCCESS", foreground="green", font=("Arial", 10, "bold"))
        self.text_widget.tag_config("WARNING", foreground="orange")
        self.text_widget.tag_config("ERROR", foreground="red", font=("Arial", 10, "bold"))
        self.text_widget.tag_config("PROGRESS", foreground="blue")
        
    def start_update_thread(self):
        """Start background thread for UI updates"""
        def update_ui():
            try:
                while True:
                    msg, tag = self.message_queue.get(timeout=0.1)
                    self.text_widget.insert(tk.END, msg + "\n", tag)
                    self.text_widget.see(tk.END)
                    
                    # Update status bar if available
                    if self.status_bar and tag in ["INFO", "SUCCESS", "ERROR"]:
                        self.status_bar.config(text=msg[:100])
            except:
                self.text_widget.after(100, update_ui)
                
        self.text_widget.after(100, update_ui)
    
    def debug(self, msg):
        self.message_queue.put((f"[DEBUG] {msg}", "DEBUG"))
        
    def info(self, msg):
        self.message_queue.put((f"[INFO] {msg}", "INFO"))
        
    def success(self, msg):
        self.message_queue.put((f"[SUCCESS] {msg}", "SUCCESS"))
        
    def warning(self, msg):
        self.message_queue.put((f"[WARNING] {msg}", "WARNING"))
        
    def error(self, msg):
        self.message_queue.put((f"[ERROR] {msg}", "ERROR"))
        
    def progress(self, msg):
        self.message_queue.put((msg, "PROGRESS"))

class DownloadManager:
    """Manages download operations with advanced features"""
    def __init__(self):
        self.active_downloads = {}
        self.download_history = []
        self.cancel_events = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def create_download_id(self):
        """Generate unique download ID"""
        return f"dl_{int(time.time() * 1000)}_{threading.get_ident()}"
        
    def cancel_download(self, download_id):
        """Cancel a specific download"""
        if download_id in self.cancel_events:
            self.cancel_events[download_id].set()
            return True
        return False
        
    def cancel_all_downloads(self):
        """Cancel all active downloads"""
        for event in self.cancel_events.values():
            event.set()

class QualityPresets:
    """Quality configuration presets"""
    
    @staticmethod
    def get_maximum_quality():
        """8K/4320p > 4K/2160p > 1440p > 1080p > 720p > best available"""
        return {
            'format': (
                'bestvideo[height>=4320][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=4320]+bestaudio/'
                'bestvideo[height>=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=2160]+bestaudio/'
                'bestvideo[height>=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=1440]+bestaudio/'
                'bestvideo[height>=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height>=1080]+bestaudio/'
                'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
            ),
            'merge_output_format': 'mp4',
            'prefer_free_formats': False,
            'format_sort': ['res:4320', 'res:2160', 'res:1440', 'res:1080', 'fps', 'vbr', 'abr'],
        }
    
    @staticmethod
    def get_audio_maximum():
        """Maximum quality audio extraction"""
        return {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',  # Maximum MP3 quality
            }],
            'prefer_ffmpeg': True,
        }
    
    @staticmethod
    def get_balanced_quality():
        """Balanced quality/size (1080p preferred)"""
        return {
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best',
            'merge_output_format': 'mp4',
        }

class YouTubeDownloaderPro:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader Pro (Enhanced Version)")
        self.root.geometry("900x700")
        
        # Initialize managers
        self.download_manager = DownloadManager()
        self.current_download_id = None
        
        # Setup UI
        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        self.check_dependencies()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_styles(self):
        """Configure ttk styles for modern UI"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TButton', background='#4CAF50')
        style.configure('Danger.TButton', background='#f44336')
        style.configure('Primary.TButton', background='#2196F3')
        
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Clear Log", command=self.clear_log)
        file_menu.add_command(label="Export History", command=self.export_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Check FFmpeg", command=self.check_ffmpeg)
        tools_menu.add_command(label="Update yt-dlp", command=self.update_ytdlp)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
    def create_widgets(self):
        """Create main UI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # URL Section
        url_frame = ttk.LabelFrame(main_frame, text="Video/Playlist URL", padding="10")
        url_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, font=('Arial', 10))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(url_frame, text="Paste", command=self.paste_url).grid(row=0, column=1)
        ttk.Button(url_frame, text="Analyze", command=self.analyze_url).grid(row=0, column=2)
        
        # Download Settings
        settings_frame = ttk.LabelFrame(main_frame, text="Download Settings", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Mode selection
        ttk.Label(settings_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W)
        self.mode_var = tk.StringVar(value="smart")
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W)
        
        ttk.Radiobutton(mode_frame, text="Smart (Auto-detect)", variable=self.mode_var, 
                       value="smart").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Single Video", variable=self.mode_var, 
                       value="single").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Playlist", variable=self.mode_var, 
                       value="playlist").pack(side=tk.LEFT, padx=5)
        
        # Quality selection
        ttk.Label(settings_frame, text="Quality:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value="maximum")
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(quality_frame, text="Maximum (8K/4K/Best)", variable=self.quality_var,
                       value="maximum").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(quality_frame, text="Balanced (1080p)", variable=self.quality_var,
                       value="balanced").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(quality_frame, text="Audio Only", variable=self.quality_var,
                       value="audio").pack(side=tk.LEFT, padx=5)
        
        # Format selection
        ttk.Label(settings_frame, text="Format:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="mp4")
        format_frame = ttk.Frame(settings_frame)
        format_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.video_format_rb = ttk.Radiobutton(format_frame, text="MP4 (Video)", 
                                               variable=self.format_var, value="mp4")
        self.video_format_rb.pack(side=tk.LEFT, padx=5)
        self.audio_format_rb = ttk.Radiobutton(format_frame, text="MP3 (Audio)", 
                                               variable=self.format_var, value="mp3")
        self.audio_format_rb.pack(side=tk.LEFT, padx=5)
        
        # Advanced options
        ttk.Label(settings_frame, text="Advanced:").grid(row=3, column=0, sticky=tk.W, pady=5)
        adv_frame = ttk.Frame(settings_frame)
        adv_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.subtitle_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(adv_frame, text="Download Subtitles", 
                       variable=self.subtitle_var).pack(side=tk.LEFT, padx=5)
        
        self.thumbnail_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv_frame, text="Embed Thumbnail", 
                       variable=self.thumbnail_var).pack(side=tk.LEFT, padx=5)
        
        self.metadata_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(adv_frame, text="Add Metadata", 
                       variable=self.metadata_var).pack(side=tk.LEFT, padx=5)
        
        # Output folder
        output_frame = ttk.LabelFrame(main_frame, text="Output Location", padding="10")
        output_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(0, weight=1)
        
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.output_entry.insert(0, str(Path.home() / "Downloads" / "YouTube"))
        
        ttk.Button(output_frame, text="Browse", command=self.browse_folder).grid(row=0, column=1)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        self.download_btn = ttk.Button(control_frame, text="🚀 Start Download", 
                                       command=self.start_download, style='Primary.TButton')
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(control_frame, text="⏸ Pause", state=tk.DISABLED,
                                    command=self.pause_download)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(control_frame, text="⏹ Cancel", state=tk.DISABLED,
                                     command=self.cancel_download, style='Danger.TButton')
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(control_frame, text="🗑 Clear All", command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bars
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        ttk.Label(progress_frame, text="Current:").grid(row=0, column=0, sticky=tk.W)
        self.current_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.current_progress.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.current_label = ttk.Label(progress_frame, text="0%")
        self.current_label.grid(row=0, column=2)
        
        ttk.Label(progress_frame, text="Overall:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.overall_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.overall_progress.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.overall_label = ttk.Label(progress_frame, text="0%")
        self.overall_label.grid(row=1, column=2, pady=5)
        
        progress_frame.columnconfigure(1, weight=1)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Download Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_container, wrap="word", height=12, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E))
        
        # Initialize logger
        self.logger = AdvancedLogger(self.log_text, self.status_bar)
        
        # Make main_frame expandable
        main_frame.rowconfigure(5, weight=1)
        
    def check_dependencies(self):
        """Check for required dependencies"""
        self.logger.info("Checking dependencies...")
        
        # Check for ffmpeg
        if shutil.which('ffmpeg'):
            self.logger.success("✓ FFmpeg found")
        else:
            self.logger.warning("⚠ FFmpeg not found - some features may be limited")
            self.logger.info("Install FFmpeg from https://ffmpeg.org/download.html (choose the build for your system).")
        
        # Check yt-dlp version
        try:
            import yt_dlp
            self.logger.success(f"✓ yt-dlp version: {yt_dlp.version.__version__}")
        except:
            self.logger.error("✗ yt-dlp not properly installed")
            
    def paste_url(self):
        """Paste URL from clipboard"""
        try:
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.root.clipboard_get())
        except:
            pass
            
    def analyze_url(self):
        """Analyze URL to get video information"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL first")
            return
            
        def analyze():
            try:
                self.logger.info("Analyzing URL...")
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': 'in_playlist',
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if 'entries' in info:
                        count = len(info['entries'])
                        self.logger.success(f"✓ Playlist detected: {info.get('title', 'Unknown')}")
                        self.logger.info(f"Videos: {count}")
                        self.mode_var.set("playlist")
                    else:
                        self.logger.success(f"✓ Video: {info.get('title', 'Unknown')}")
                        self.logger.info(f"Duration: {info.get('duration', 0) // 60} minutes")
                        self.logger.info(f"Uploader: {info.get('uploader', 'Unknown')}")
                        
                        # Check available qualities
                        formats = info.get('formats', [])
                        resolutions = set()
                        for f in formats:
                            if f.get('height'):
                                resolutions.add(f['height'])
                        
                        if resolutions:
                            max_res = max(resolutions)
                            self.logger.info(f"Max Resolution: {max_res}p")
                            if max_res >= 2160:
                                self.logger.success("✓ 4K/8K available")
                                
                        self.mode_var.set("single")
                        
            except Exception as e:
                self.logger.error(f"Analysis failed: {str(e)}")
                
        threading.Thread(target=analyze, daemon=True).start()
        
    def browse_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            
    def build_ydl_opts(self, url, download_id):
        """Build yt-dlp options based on settings"""
        output_dir = self.output_entry.get()
        os.makedirs(output_dir, exist_ok=True)
        
        cancel_event = threading.Event()
        self.download_manager.cancel_events[download_id] = cancel_event
        
        # Base options
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(playlist_title)s/%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': False,
            'no_color': True,
            'retries': 10,
            'fragment_retries': 10,
            'concurrent_fragment_downloads': 5,
            'buffersize': 1024 * 64,  # 64KB buffer
            'http_chunk_size': 10485760,  # 10MB chunks
            'ratelimit': None,  # No rate limit for maximum speed
            'throttledratelimit': None,
            'logger': self.logger,
            'progress_hooks': [self.create_progress_hook(download_id, cancel_event)],
        }
        
        # Mode specific options
        if self.mode_var.get() == "single":
            ydl_opts['noplaylist'] = True
            
        # Quality and format options
        quality = self.quality_var.get()
        format_choice = self.format_var.get()
        
        if quality == "audio" or format_choice == "mp3":
            ydl_opts.update(QualityPresets.get_audio_maximum())
        elif quality == "maximum":
            ydl_opts.update(QualityPresets.get_maximum_quality())
        elif quality == "balanced":
            ydl_opts.update(QualityPresets.get_balanced_quality())
            
        # Post-processors
        postprocessors = []
        
        if self.thumbnail_var.get() and format_choice == "mp4":
            postprocessors.append({
                'key': 'EmbedThumbnail',
                'already_have_thumbnail': False,
            })
            ydl_opts['writethumbnail'] = True
            
        if self.metadata_var.get():
            postprocessors.append({
                'key': 'FFmpegMetadata',
                'add_chapters': True,
            })
            
        if self.subtitle_var.get():
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = ['en', 'en-US']
            postprocessors.append({
                'key': 'FFmpegEmbedSubtitle',
                'already_have_subtitle': False,
            })
            
        # Ensure proper merging
        if format_choice == "mp4" and quality != "audio":
            postprocessors.append({
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            })
            
        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors
            
        return ydl_opts
        
    def create_progress_hook(self, download_id, cancel_event):
        """Create progress hook for download tracking"""
        def hook(d):
            if cancel_event.is_set():
                raise yt_dlp.utils.DownloadError("Download canceled by user")
                
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                if total > 0:
                    percent = (downloaded / total) * 100
                    self.update_progress(percent, downloaded, total, speed, eta)
                    
                    # Log download speed and ETA
                    if speed:
                        speed_mb = speed / (1024 * 1024)
                        eta_str = f"{eta // 60}:{eta % 60:02d}" if eta else "Unknown"
                        self.logger.progress(f"Speed: {speed_mb:.2f} MB/s | ETA: {eta_str}")
                        
            elif d['status'] == 'finished':
                filename = d.get('filename', 'Unknown')
                self.logger.success(f"✓ Downloaded: {os.path.basename(filename)}")
                self.update_progress(100)
                
            elif d['status'] == 'error':
                self.logger.error(f"✗ Download error: {d.get('error', 'Unknown error')}")
                
        return hook
        
    def update_progress(self, percent, downloaded=0, total=0, speed=0, eta=0):
        """Update progress bars"""
        def update():
            self.current_progress['value'] = percent
            self.current_label['text'] = f"{percent:.1f}%"
            
            if total > 0:
                size_mb = total / (1024 * 1024)
                downloaded_mb = downloaded / (1024 * 1024)
                self.status_bar['text'] = f"Downloading: {downloaded_mb:.1f}/{size_mb:.1f} MB ({percent:.1f}%)"
                
        self.root.after(0, update)
        
    def start_download(self):
        """Start the download process"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
            
        # Validate URL
        youtube_regex = r'(https?://)?(www\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)/.+'
        if not re.match(youtube_regex, url):
            messagebox.showerror("Error", "Invalid YouTube URL")
            return
            
        # Create download ID
        download_id = self.download_manager.create_download_id()
        self.current_download_id = download_id
        
        # Update UI
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.logger.info("=" * 50)
        self.logger.info("Starting new download session")
        self.logger.info(f"URL: {url}")
        self.logger.info(f"Quality: {self.quality_var.get()}")
        self.logger.info(f"Format: {self.format_var.get()}")
        self.logger.info("=" * 50)
        
        def download_thread():
            try:
                ydl_opts = self.build_ydl_opts(url, download_id)
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    start_time = time.time()
                    ydl.download([url])
                    
                    elapsed = time.time() - start_time
                    self.logger.success(f"✓ Download completed in {elapsed:.1f} seconds!")
                    self.download_manager.download_history.append({
                        'url': url,
                        'timestamp': datetime.now().isoformat(),
                        'duration': elapsed,
                        'status': 'completed'
                    })
                    
            except yt_dlp.utils.DownloadError as e:
                if "canceled" in str(e).lower() or "cancelled" in str(e).lower():
                    self.logger.warning("Download canceled by user")
                else:
                    self.logger.error(f"Download error: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                logging.exception("Download failed")
            finally:
                # Reset UI
                self.root.after(0, self.reset_ui)
                
                # Clean up
                if download_id in self.download_manager.cancel_events:
                    del self.download_manager.cancel_events[download_id]
                    
        # Start download in background
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
        self.download_manager.active_downloads[download_id] = thread
        
    def pause_download(self):
        """Pause download (placeholder for future implementation)"""
        self.logger.info("Pause feature will be available in a future update")

    def cancel_download(self):
        """Cancel current download"""
        if self.current_download_id:
            if self.download_manager.cancel_download(self.current_download_id):
                self.logger.warning("Canceling download...")
                self.cancel_btn.config(state=tk.DISABLED)

    def reset_ui(self):
        """Reset UI after download"""
        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.current_progress['value'] = 0
        self.current_label['text'] = "0%"
        self.overall_progress['value'] = 0
        self.overall_label['text'] = "0%"
        self.status_bar['text'] = "Ready"
        
    def clear_log(self):
        """Clear the log text widget"""
        self.log_text.delete("1.0", tk.END)
        self.logger.info("Log cleared")
        
    def clear_all(self):
        """Clear all inputs and logs"""
        self.url_entry.delete(0, tk.END)
        self.clear_log()
        self.reset_ui()
        
    def check_ffmpeg(self):
        """Check FFmpeg installation"""
        if shutil.which('ffmpeg'):
            ffmpeg_path = shutil.which('ffmpeg')
            messagebox.showinfo("FFmpeg Status", f"FFmpeg is installed\nPath: {ffmpeg_path}")
        else:
            result = messagebox.askyesno(
                "FFmpeg Not Found",
                "FFmpeg is not installed or not in PATH.\n"
                "FFmpeg is required for video/audio conversion and merging.\n\n"
                "Would you like to open the FFmpeg download page?"
            )
            if result:
                import webbrowser
                webbrowser.open("https://ffmpeg.org/download.html")
                
    def update_ytdlp(self):
        """Update yt-dlp to latest version"""
        def update():
            try:
                self.logger.info("Updating yt-dlp...")
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.logger.success("✓ yt-dlp updated successfully!")
                    messagebox.showinfo("Update Complete", "yt-dlp has been updated to the latest version")
                else:
                    self.logger.error(f"Update failed: {result.stderr}")
            except Exception as e:
                self.logger.error(f"Update error: {str(e)}")
                
        threading.Thread(target=update, daemon=True).start()
        
    def export_history(self):
        """Export download history to JSON file"""
        if not self.download_manager.download_history:
            messagebox.showinfo("No History", "No download history to export")
            return
            
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.download_manager.download_history, f, indent=2)
                messagebox.showinfo("Export Complete", f"History exported to {filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
                
    def show_about(self):
        """Show about dialog"""
        about_text = """YouTube Downloader Pro (Enhanced Version)

Version: 1.0.0
Author: Advanced Development Team

Features:
- Maximum quality downloads (8K / 4K / 1080p)
- Smart quality detection
- Concurrent downloads
- Advanced error handling
- Subtitle and metadata support
- Real-time progress tracking

Powered by:
- yt-dlp (downloading)
- FFmpeg (processing)
- tkinter (GUI)

For best results, ensure FFmpeg is installed."""
        messagebox.showinfo("About", about_text)
        
    def on_closing(self):
        """Handle window closing event"""
        if self.download_manager.active_downloads:
            result = messagebox.askyesno(
                "Active Downloads",
                "There are active downloads. Are you sure you want to exit?"
            )
            if not result:
                return
                
        # Cancel all downloads
        self.download_manager.cancel_all_downloads()
        
        # Destroy window
        self.root.destroy()


class DownloadQueue:
    """Advanced download queue management"""
    def __init__(self, max_concurrent=3):
        self.queue = queue.Queue()
        self.max_concurrent = max_concurrent
        self.active_downloads = []
        self.completed_downloads = []
        self.failed_downloads = []
        
    def add_to_queue(self, url, options):
        """Add a download to the queue"""
        download_item = {
            'id': f"dl_{int(time.time() * 1000)}",
            'url': url,
            'options': options,
            'status': 'queued',
            'added_time': datetime.now()
        }
        self.queue.put(download_item)
        return download_item['id']
        
    def get_queue_size(self):
        """Get current queue size"""
        return self.queue.qsize()
        
    def process_queue(self):
        """Process downloads from queue"""
        while len(self.active_downloads) < self.max_concurrent and not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                self.start_download(item)
            except queue.Empty:
                break


class VideoAnalyzer:
    """Analyze video information before download"""
    @staticmethod
    def get_video_info(url):
        """Get detailed video information"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Extract relevant information
                video_info = {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', '')[:500],
                    'thumbnail': info.get('thumbnail', ''),
                    'formats': []
                }
                
                # Get available formats
                for f in info.get('formats', []):
                    if f.get('height'):
                        format_info = {
                            'format_id': f.get('format_id'),
                            'ext': f.get('ext'),
                            'height': f.get('height'),
                            'fps': f.get('fps'),
                            'vcodec': f.get('vcodec'),
                            'acodec': f.get('acodec'),
                            'filesize': f.get('filesize', 0),
                            'tbr': f.get('tbr', 0)  # Total bitrate
                        }
                        video_info['formats'].append(format_info)
                        
                # Sort formats by quality
                video_info['formats'].sort(key=lambda x: (x['height'] or 0, x['tbr'] or 0), reverse=True)
                
                return video_info
                
        except Exception as e:
            return {'error': str(e)}


class SettingsManager:
    """Manage application settings"""
    def __init__(self):
        self.settings_file = Path.home() / ".youtube_downloader_pro" / "settings.json"
        self.settings_file.parent.mkdir(exist_ok=True)
        self.settings = self.load_settings()
        
    def load_settings(self):
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default settings
        return {
            'output_folder': str(Path.home() / "Downloads" / "YouTube"),
            'quality': 'maximum',
            'format': 'mp4',
            'subtitles': False,
            'thumbnail': True,
            'metadata': True,
            'concurrent_downloads': 3,
            'max_retries': 10,
            'buffer_size': 65536,
            'chunk_size': 10485760
        }
        
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")
            
    def get(self, key, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
        
    def set(self, key, value):
        """Set a setting value"""
        self.settings[key] = value
        self.save_settings()


def main():
    """Main entry point"""
    # Check Python version
    if sys.version_info < (3, 10):
        print("This application requires Python 3.10 or higher")
        sys.exit(1)
    
    # Check for required packages
    required_packages = ['yt_dlp', 'tkinter']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install yt-dlp")
        sys.exit(1)
    
    # Create and run application
    root = tk.Tk()
    app = YouTubeDownloaderPro(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Set minimum window size
    root.minsize(800, 600)
    
    # Run application
    root.mainloop()


if __name__ == "__main__":
    main()