"""RunPod serverless worker entrypoint.

The `handler(event)` function receives JSON from RunPod and must return JSON serializable output.
Documentation: https://docs.runpod.io/serverless/workers/custom-worker

Build image and deploy as a custom worker. Environment variables (API keys, S3 bucket) are
loaded automatically from `.env` inside the image.
"""
from __future__ import annotations

import os
import logging
import traceback
from pathlib import Path
from typing import Any, Dict, List

from image_generator import FluxImageGenerator  # noqa: E402  pylint: disable=wrong-import-position

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    force=True,
)
logger = logging.getLogger(__name__)

# Instantiate once (cold-start) and reuse across invocations
logger.info("Loading model …")
_GENERATOR = FluxImageGenerator()
logger.info("Model loaded successfully.")

logger.info("HF token present: %s", bool(os.getenv("HUGGINGFACE_HUB_TOKEN")))
logger.info("S3 bucket: %s", os.getenv("S3_BUCKET"))

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
        logger.info("Generating %s image(s) for prompt: %s", num_images, prompt)
        paths = _GENERATOR.generate(prompt, num_images=num_images, seed=seed)
        logger.info("Generation finished; %s file(s)", len(paths))
    except Exception as exc:  # noqa: BLE001 broaden for logging
        logger.error("Generation failed: %s", exc)
        logger.debug("%s", traceback.format_exc())
        return {"error": str(exc)}

    files: List[str]
    if isinstance(paths[0], str):
        # image_generator already returned a list of strings (local paths or S3 URLs)
        files = paths
    else:
        # We got Path objects – return just the filenames
        files = [p.name for p in paths]

    return {"files": files}



# ---------------------------------------------------------------------------
# When executed directly (e.g., `python -u worker.py`), start the RunPod loop.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import runpod

    runpod.serverless.start({"handler": handler})
