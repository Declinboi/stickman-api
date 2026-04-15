import os
import logging
import tempfile
import inspect  # ← add here
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from cloudinary_helper import upload_output_video
from fight_generator import generate_fight
import motion_curves

print("motion_curves path:", inspect.getfile(motion_curves))
print("has block_curve:", hasattr(motion_curves, "block_curve"))


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    job_id: str
    description: str  # natural language fight description


class GenerateResponse(BaseModel):
    job_id: str
    output_video_url: str
    message: str


app = FastAPI(title="Stickman Fight Generator")


@app.get("/health")
def health():
    return {"status": "ok", "service": "stickman-generator"}


@app.post("/process", response_model=GenerateResponse)
def process(req: GenerateRequest):
    output_path: str | None = None

    try:
        logger.info("[%s] Generating fight: %s", req.job_id, req.description[:80])

        output_path = generate_fight(req.description, req.job_id)

        logger.info("[%s] Uploading to Cloudinary...", req.job_id)
        output_url = upload_output_video(output_path, req.job_id)

        return GenerateResponse(
            job_id=req.job_id,
            output_video_url=output_url,
            message="Fight generated successfully",
        )

    except Exception as e:
        logger.error("[%s] Failed: %s", req.job_id, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Generation failed", "reason": str(e)},
        )

    finally:
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
