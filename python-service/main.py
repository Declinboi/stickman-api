import os
import logging
import tempfile
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from cloudinary_helper import download_video, upload_output_video
from video_processor import process_video
load_dotenv()
# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)
# ── Request / Response schemas ────────────────────────────────────────────────
class ProcessRequest(BaseModel):
    job_id: str
    input_video_url: str
class ProcessResponse(BaseModel):
    job_id: str
    output_video_url: str
    message: str
# ── App ───────────────────────────────────────────────────────────────────────
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
    NOTE: This is intentionally a sync def — FastAPI runs it in a threadpool
    automatically, which is appropriate since NestJS controls job dispatch rate
    and prevents concurrent overload.
    """
    input_path: str | None = None
    output_path: str | None = None
    try:
        logger.info("[%s] Downloading input video...", req.job_id)
        input_path = download_video(req.input_video_url)
        logger.info("[%s] Running pose estimation...", req.job_id)
        output_path = process_video(input_path, req.job_id)
        logger.info("[%s] Uploading output to Cloudinary...", req.job_id)
        output_url = upload_output_video(output_path, req.job_id)
        logger.info("[%s] Done — %s", req.job_id, output_url)
        return ProcessResponse(
            job_id=req.job_id,
            output_video_url=output_url,
            message="Processing completed successfully",
        )
    except ValueError as e:
        # Validation errors (bad Content-Type, file too large, etc.)
        logger.warning("[%s] Validation error: %s", req.job_id, e)
        raise HTTPException(
            status_code=422,
            detail={"error": "Invalid input", "reason": str(e)},
        )
    except Exception as e:
        logger.error("[%s] Processing failed: %s", req.job_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Processing failed", "reason": str(e)},
        )
    finally:
        # ── Always clean up temp files ────────────────────────────────────────
        for path, label in [(input_path, "input"), (output_path, "output")]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.info(
                        "[%s] Cleaned up %s temp file: %s",
                        req.job_id, label, path,
                    )
                except OSError as cleanup_err:
                    logger.warning(
                        "[%s] Failed to delete %s temp file %s: %s",
                        req.job_id, label, path, cleanup_err,
                    )
