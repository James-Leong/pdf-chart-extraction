"""Utility functions for PDF chart extraction."""

from __future__ import annotations

import re
from typing import Any


def looks_like_toc_line(line: str) -> bool:
    """Check if a line looks like a table of contents entry."""
    normalized = line.replace("　", " ")
    return bool(re.search(r"[.·]{4,}\s*\d+\s*$", normalized))


def safe_filename(text: str) -> str:
    """Convert text to a safe filename component."""
    # Allow CJK characters, alphanumeric, and common safe chars
    return re.sub(r"[^0-9A-Za-z一-鿿._-]+", "_", text)


def format_bbox(bbox: Any) -> tuple[float, float, float, float] | None:
    """Format a bbox-like object to a tuple."""
    if bbox is None:
        return None
    if hasattr(bbox, "x0"):
        return (
            round(float(bbox.x0), 2),
            round(float(bbox.y0), 2),
            round(float(bbox.x1), 2),
            round(float(bbox.y1), 2),
        )
    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
        return (
            round(float(bbox[0]), 2),
            round(float(bbox[1]), 2),
            round(float(bbox[2]), 2),
            round(float(bbox[3]), 2),
        )
    return None


def union_rects(rects: list[Any]) -> Any:
    """Union multiple rects into one."""
    if not rects:
        raise ValueError("Cannot union empty rect list")
    result = rects[0]
    for r in rects[1:]:
        result = _union_two(result, r)
    return result


def _union_two(a: Any, b: Any) -> Any:
    """Union two rects."""
    result = type(a)(a)  # copy
    if hasattr(result, "include_rect"):
        result.include_rect(b)
        return result
    # Fallback for plain tuples
    return (
        min(a[0], b[0]),
        min(a[1], b[1]),
        max(a[2], b[2]),
        max(a[3], b[3]),
    )


def pad_rect(rect: Any, bounds: Any, padding: float) -> Any:
    """Pad a rect by padding points, clamped to bounds."""
    if hasattr(rect, "x0"):
        # fitz.Rect style
        import fitz

        padded = fitz.Rect(
            rect.x0 - padding,
            rect.y0 - padding,
            rect.x1 + padding,
            rect.y1 + padding,
        )
        return padded & bounds
    # Plain tuple fallback
    return (
        max(bounds[0], rect[0] - padding),
        max(bounds[1], rect[1] - padding),
        min(bounds[2], rect[2] + padding),
        min(bounds[3], rect[3] + padding),
    )


def build_crop_bbox(
    caption_bbox: Any,
    content_bbox: Any,
    page_rect: Any,
    padding: float = 12.0,
) -> Any:
    """Build a crop bbox that includes both caption and content."""
    import fitz

    left = min(caption_bbox.x0, content_bbox.x0) - padding
    right = max(caption_bbox.x1, content_bbox.x1) + padding

    if caption_bbox.y1 <= content_bbox.y0:
        # Caption above content
        top = caption_bbox.y0 - 4
        bottom = content_bbox.y1 + 8
    elif caption_bbox.y0 >= content_bbox.y1:
        # Caption below content
        top = content_bbox.y0 - 8
        bottom = caption_bbox.y1 + 4
    else:
        # Overlapping or unknown
        top = min(caption_bbox.y0, content_bbox.y0) - 8
        bottom = max(caption_bbox.y1, content_bbox.y1) + 8

    return fitz.Rect(left, top, right, bottom) & page_rect
