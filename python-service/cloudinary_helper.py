import os
import logging
import cloudinary
import cloudinary.uploader
import cloudinary.exceptions
import requests
import tempfile
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)
# ── Max allowed input video size (500 MB) ───────────────────────────────────
MAX_VIDEO_BYTES = 500 * 1024 * 1024
# ── Cloudinary config (runs once at import time) ─────────────────────────────
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)
# ── Download ──────────────────────────────────────────────────────────────────
@retry(
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, OSError)
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def download_video(url: str, suffix: str = ".mp4") -> str:
    """
    Download a video from a URL into a temp file.
    - Retries up to 3 times with exponential backoff on network errors.
    - Validates Content-Type header.
    - Enforces a 500 MB size cap.
    - Cleans up the temp file if a write error occurs mid-stream.
    Returns the temp file path.
    """
    logger.info("Downloading video from URL: %s", url)
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()
    # ── Content-Type guard ───────────────────────────────────────────────────
    content_type = response.headers.get("Content-Type", "")
    if "video" not in content_type and "octet-stream" not in content_type:
        raise ValueError(
            f"Unexpected Content-Type from URL: '{content_type}'. "
            "Expected a video or binary stream."
        )
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    bytes_written = 0
    try:
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:           # skip keep-alive empty chunks
                continue
            bytes_written += len(chunk)
            if bytes_written > MAX_VIDEO_BYTES:
                raise ValueError(
                    f"Input video exceeds maximum allowed size of "
                    f"{MAX_VIDEO_BYTES // (1024 * 1024)} MB."
                )
            tmp.write(chunk)
        tmp.close()
    except Exception:
        # ── Clean up temp file on any mid-stream failure ─────────────────────
        tmp.close()
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
            logger.warning("Cleaned up partial temp file: %s", tmp.name)
        raise
    logger.info(
        "Download complete — %.2f MB written to %s",
        bytes_written / (1024 * 1024),
        tmp.name,
    )
    return tmp.name
# ── Upload ─────────────────────────────────────��──────────────────────────────
@retry(
    retry=retry_if_exception_type(
        (cloudinary.exceptions.Error, Exception)
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def upload_output_video(file_path: str, job_id: str) -> str:
    """
    Upload the processed stickman video to Cloudinary.
    - Retries up to 3 times with exponential backoff on Cloudinary errors.
    Returns the secure URL.
    """
    logger.info("Uploading output video for job %s from %s", job_id, file_path)
    result = cloudinary.uploader.upload(
        file_path,
        resource_type="video",
        folder="stickman/outputs",
        public_id=f"output-{job_id}",
        overwrite=True,
    )
    secure_url = result.get("secure_url")
    if not secure_url:
        raise RuntimeError(
            f"Cloudinary upload for job {job_id} returned no secure_url."
        )
    logger.info("Upload complete for job %s — %s", job_id, secure_url)
    return secure_url