from __future__ import annotations

import sys

def _check_deps() -> None:
    missing: list[str] = []
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")

    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print(f"Install with:  pip install {' '.join(missing)}")
        sys.exit(1)

if __name__ == "__main__":
    _check_deps()
    from ytdlp_gui.app import main

    main()
