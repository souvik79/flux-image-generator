"""RunPod serverless worker entrypoint.

The `handler(event)` function receives JSON from RunPod and must return JSON serializable output.
Documentation: https://docs.runpod.io/serverless/workers/custom-worker

Build image and deploy as a custom worker. Environment variables (API keys, S3 bucket) are
loaded automatically from `.env` inside the image.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

# Attempt to load .env bundled with the image
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=False)

from image_generator import FluxImageGenerator  # noqa: E402  pylint: disable=wrong-import-position

# Instantiate once (cold-start) and reuse across invocations
_GENERATOR = FluxImageGenerator()


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """RunPod will invoke this function with an *event* dict.

    Expected event structure:
    {
        "input": {
            "prompt": "text prompt",
            "num_images": 2,   # optional, 1-6
            "seed": 42         # optional
        }
    }
    """
    input_data = event.get("input", {})
    prompt = input_data.get("prompt")
    if not prompt:
        return {"error": "'prompt' is required"}

    num_images = int(input_data.get("num_images", 1))
    seed = input_data.get("seed")

    # Enforce range 1-6
    num_images = max(1, min(num_images, 6))

    try:
        paths = _GENERATOR.generate(prompt, num_images=num_images, seed=seed)
    except RuntimeError as exc:  # OOM or other
        return {"error": str(exc)}

    if paths:
        files: List[str] = [p.name for p in paths]
    else:  # deleted locally, assume S3 upload
        bucket = os.getenv("S3_BUCKET")
        prefix = os.getenv("S3_PREFIX", "")
        files = [f"s3://{bucket}/{prefix}"] if bucket else []

    return {"files": files}


# RunPod python runtime looks for `handler` symbol automatically if using default CMD.
