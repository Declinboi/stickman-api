import cloudinary
import cloudinary.uploader
import requests
import tempfile
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def download_video(url: str, suffix: str = ".mp4") -> str:
    """Download a video from a URL into a temp file. Returns the temp file path."""
    response = requests.get(url, stream=True, timeout=120)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    for chunk in response.iter_content(chunk_size=8192):
        tmp.write(chunk)
    tmp.close()

    return tmp.name


def upload_output_video(file_path: str, job_id: str) -> str:
    """Upload the processed stickman video to Cloudinary. Returns secure URL."""
    result = cloudinary.uploader.upload(
        file_path,
        resource_type="video",
        folder="stickman/outputs",
        public_id=f"output-{job_id}",
        overwrite=True,
    )
    return result["secure_url"]