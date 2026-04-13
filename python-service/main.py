import os
import tempfile
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv

from cloudinary_helper import download_video, upload_output_video
from video_processor import process_video

load_dotenv()


# ── Request / Response schemas ──────────────────────────────────────────────

class ProcessRequest(BaseModel):
    job_id: str
    input_video_url: str


class ProcessResponse(BaseModel):
    job_id: str
    output_video_url: str
    message: str


# ── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="Stickman Pose Estimation Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "stickman-python"}


@app.post("/process", response_model=ProcessResponse)
def process(req: ProcessRequest):
    """
    Main endpoint called by NestJS queue consumer.
    1. Downloads input video from Cloudinary
    2. Runs pose estimation + stickman rendering
    3. Uploads output video back to Cloudinary
    4. Returns the output video URL
    """
    input_path  = None
    output_path = None

    try:
        print(f"[{req.job_id}] Downloading input video...")
        input_path = download_video(req.input_video_url)

        print(f"[{req.job_id}] Running pose estimation...")
        output_path = process_video(input_path, req.job_id)

        print(f"[{req.job_id}] Uploading output to Cloudinary...")
        output_url = upload_output_video(output_path, req.job_id)

        print(f"[{req.job_id}] Done — {output_url}")

        return ProcessResponse(
            job_id=req.job_id,
            output_video_url=output_url,
            message="Processing completed successfully",
        )

    except Exception as e:
        print(f"[{req.job_id}] ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Clean up temp files
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)