"""Video processing helpers based on ffmpeg."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class FFmpegError(RuntimeError):
    """Raised when ffmpeg commands fail."""


def ensure_ffmpeg_available() -> str:
    """Resolve a valid ffmpeg binary path.

    Resolution order:
    1) FFMPEG_BIN env var
    2) ffmpeg in PATH
    3) imageio-ffmpeg bundled binary
    """
    ffmpeg_bin = os.getenv("FFMPEG_BIN")
    if ffmpeg_bin:
        return ffmpeg_bin

    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        return ffmpeg_bin

    try:
        import imageio_ffmpeg  # pylint: disable=import-outside-toplevel

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - fallback failure
        raise FFmpegError("ffmpeg binary is not available") from exc


def save_upload_to_file(content: bytes, suffix: str = ".mp4") -> str:
    """Persist uploaded bytes into a temporary file and return the path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise
    return path


def extract_frames(video_path: str, fps: float, output_dir: str) -> list[str]:
    """Extract video frames to output_dir and return sorted frame paths."""
    ffmpeg_bin = ensure_ffmpeg_available()
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    frame_pattern = str(Path(output_dir) / "frame_%06d.jpg")
    command = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"fps={fps}",
        frame_pattern,
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise FFmpegError(completed.stderr.strip() or "ffmpeg failed extracting frames")

    return sorted(str(path) for path in Path(output_dir).glob("frame_*.jpg"))
