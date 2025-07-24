"""api.py
FastAPI server exposing a /generate endpoint that wraps FluxImageGenerator.
Run with:
    uvicorn api:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

from image_generator import FluxImageGenerator

app = FastAPI(title="Flux Image Generator API")

# Instantiate once at startup; reuse across requests to keep the model in GPU/CPU memory
_generator = FluxImageGenerator()

# ----------------------------- Models -----------------------------

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Raw text prompt to feed into FLUX model")
    num_images: int = Field(1, ge=1, le=6, description="Number of images (1-6)")
    seed: int | None = Field(None, description="Optional random seed for reproducibility")

class GenerateResponse(BaseModel):
    files: List[str] = Field(..., description="List of S3 keys or local filenames")

# ---------------------------- Routes ------------------------------

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    # Enforce limits (Pydantic already checks 1-6)
    try:
        paths = _generator.generate(
            req.prompt, num_images=req.num_images, seed=req.seed
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Build response paths relative to outputs/ dir or S3 keys
    if paths:
        files = [p.name for p in paths]
    else:
        # If DELETE_LOCAL_AFTER_S3=true we have no local files; return the S3 prefix instead
        bucket = os.getenv("S3_BUCKET")
        prefix = os.getenv("S3_PREFIX", "")
        files = [f"s3://{bucket}/{prefix}"] if bucket else []

    return GenerateResponse(files=files)

# --------------------------- Health -------------------------------

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
