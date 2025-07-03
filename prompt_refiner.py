"""prompt_refiner.py
Refines a user-supplied prompt via OpenAI’s chat-completion API so it is better
suited for photorealistic diffusion models.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables (looks for a .env file in project root)
load_dotenv()


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:  # cached so we don’t re-create HTTP pool each call
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not set – add it to your shell env or a .env file"
        )
    return OpenAI(api_key=api_key)


def refine_prompt(raw_prompt: str, *, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    """Return a single, detailed prompt optimised for image generation."""
    system_msg = (
        "You are an expert prompt engineer for text-to-image diffusion models. "
        "Take the user's raw idea and craft ONE vivid, concrete, photorealistic "
        "prompt. Avoid camera brands, embed lighting, mood, and composition. "
        "Return ONLY the improved prompt and nothing else."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": raw_prompt},
        ],
    )
    return response.choices[0].message.content.strip()
