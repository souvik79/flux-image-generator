"""naming.py
Utility helpers for building consistent, URL-safe filenames for generated images.
"""
from __future__ import annotations

def generate_filename(
    category: str,
    service: str,
    style: str,
    aspect_ratio: str,
    ext: str = "webp",
) -> str:
    """Return a slugified filename like `food-delivery-hero-3d-16x9.webp`.

    All spaces are replaced with `-`, strings are lower-cased, slashes become dashes, and
    the *:* in the *aspect_ratio* (e.g. "16:9") is replaced with `x`.
    """
    base = (
        f"{category.strip().lower()}-"
        f"{service.strip().lower()}-"
        f"{style.strip().lower()}-"
        f"{aspect_ratio.strip().lower().replace(':', 'x')}"
    )
    safe_base = (
        base.replace(" ", "-")
        .replace("/", "-")
        .replace("\\", "-")
    )
    return f"{safe_base}.{ext.lstrip('.').lower()}"

# ---------------------------------------------------------------------------
# Sheet-specific helper

def filename_from_row(row: dict[str, str], *, ext: str = "webp") -> str:
    """Return filename like `IMG008-landscaping-irrigation-systems-3d-rendered-570x570.webp`.

    Expected column names (case-insensitive):
      • Image ID          (mandatory)
      • Industry          (mandatory)
      • Parent Subject    (mandatory)
      • Style             (optional)
      • Image Size        (optional)

    All pieces are slugified (lower-case, spaces→dash, slash→dash). Empty pieces are skipped.
    """

    def slug(text: str) -> str:
        return (
            text.strip().lower()
            .replace(" ", "-")
            .replace("/", "-")
            .replace("\\", "-")
        )

    image_id = row.get("Image ID") or row.get("ImageID") or "img"
    industry = row.get("Industry", "")
    parent   = row.get("Parent Subject", "")
    style    = row.get("Style", "")
    size     = row.get("Image Size", "")

    parts = [slug(p) for p in (industry, parent, style, size) if p]
    base  = f"{image_id}-{ '-'.join(parts) }".strip("-")

    return f"{base}.{ext.lstrip('.').lower()}"
