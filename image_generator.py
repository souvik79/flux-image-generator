"""image_generator.py
Generate images from a text prompt using the FLUX.1 dev diffusion model.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

import torch
from diffusers import AutoPipelineForText2Image
from dotenv import load_dotenv

# Constants
_MODEL_ID = "black-forest-labs/FLUX.1-dev"
if torch.cuda.is_available():
    _DEVICE = "cuda"
elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
    # Apple Silicon / Metal backend
    _DEVICE = "mps"
else:
    _DEVICE = "cpu"

# Load env vars (including optional HUGGINGFACE_HUB_TOKEN)
load_dotenv()

_OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
_OUTPUT_DIR.mkdir(exist_ok=True)


class FluxImageGenerator:
    def __init__(self, model_id: str = _MODEL_ID, device: str = _DEVICE):
        # float16 on CUDA, but stick to float32 on Apple Silicon (MPS) for ops coverage
        if device == "cuda":
            torch_dtype = torch.float16
        else:
            torch_dtype = torch.float32

        auth_token = os.getenv("HUGGINGFACE_HUB_TOKEN")

        # FLUX.1-dev is an SDXL-based model, so we use the automatic text-to-image
        # pipeline loader which will pick StableDiffusionXLPipeline under the hood.
        self.pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            # keep default weights; we will cast after loading
            safety_checker=None,  # FLUX ships without explicit safety checker
            token=auth_token if auth_token else None,
        )

        # Memory-saving tweaks so the model fits on 16 GB GPUs like RTX A4000
        if device == "cuda":
            self.pipe.enable_attention_slicing()   # reduce attention footprint
            self.pipe.enable_vae_tiling()          # reduce VAE memory
            # If VRAM is still insufficient, off-load parts of the model to CPU.
            # This keeps peak GPU usage under ~8 GB on SDXL at the cost of ~2× speed.
            self.pipe.enable_model_cpu_offload()  # 24 GB

        # Keep the scheduler that FLUX provides; overriding can break custom sigma schedules
        self.device = device

    @torch.inference_mode()
    def generate(self, prompt: str, *, num_images: int = 1, seed: int | None = None) -> List[Path]:
        """Generate *num_images* images and return file paths."""
        generator = torch.Generator(device=self.device)
        if seed is not None:
            generator = generator.manual_seed(seed)

        images = self.pipe(
            prompt=prompt,
            num_inference_steps=30,
            num_images_per_prompt=num_images,
            guidance_scale=7.0,
            generator=generator,
        ).images

        saved_paths: List[Path] = []
        base = prompt[:50].replace(" ", "_") or "image"
        for idx, img in enumerate(images, 1):
            filename = f"{base}_{idx}.png"
            path = _OUTPUT_DIR / filename
            img.save(path)
            saved_paths.append(path)
        return saved_paths
