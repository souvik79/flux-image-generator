"""main.py
CLI entry-point for the Prompt-to-Image generator.

Usage (after activating venv and installing deps):

    python main.py "a cat on a bench"

Environment:
    OPENAI_API_KEY must be set (shell or .env).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from prompt_refiner import refine_prompt
from image_generator import FluxImageGenerator


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prompt-to-Image generator (CLI)")
    parser.add_argument("prompt", type=str, help="Raw prompt (quote if it has spaces)")
    parser.add_argument("--num", "-n", type=int, default=4, help="Number of images to generate")
    parser.add_argument("--seed", type=int, default=None, help="Optional random seed")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    print("Refining prompt via OpenAI…", flush=True)
    refined = refine_prompt(args.prompt)
    print("\nRaw prompt:     ", args.prompt)
    print("Refined prompt: ", refined)

    print("\nGenerating images with FLUX.1-dev…")
    generator = FluxImageGenerator()
    paths = generator.generate(refined, num_images=args.num, seed=args.seed)

    print("\nSaved:")
    for p in paths:
        print(" •", p.relative_to(Path.cwd()))


if __name__ == "__main__":
    main(sys.argv[1:])
