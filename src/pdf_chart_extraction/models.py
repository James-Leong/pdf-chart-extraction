"""Data models for PDF chart extraction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal


class AssetKind(str, Enum):
    """Type of extracted asset."""

    FIGURE = "figure"
    TABLE = "table"


class CaptionPosition(str, Enum):
    """Relative position of caption to content."""

    ABOVE = "above"
    BELOW = "below"
    OVERLAP = "overlap"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ChartAsset:
    """A detected and extracted chart/figure/table asset from a PDF."""

    kind: Literal["figure", "table"]
    label: str
    title: str
    pdf_page: int
    caption_bbox: tuple[float, float, float, float]
    content_bbox: tuple[float, float, float, float] | None
    image_path: str | None
    caption_position: Literal["above", "below", "overlap", "unknown"]
    detection_method: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to plain dictionary."""
        return asdict(self)


@dataclass
class ExtractionResult:
    """Result of extracting charts from a PDF."""

    pdf_path: str
    output_dir: str
    assets: list[ChartAsset] = field(default_factory=list)
    total_pages: int = 0

    def figures(self) -> list[ChartAsset]:
        """Return only figure assets."""
        return [a for a in self.assets if a.kind == "figure"]

    def tables(self) -> list[ChartAsset]:
        """Return only table assets."""
        return [a for a in self.assets if a.kind == "table"]

    def save_index(self, path: Path | None = None) -> Path:
        """Save asset index as JSON."""
        import json

        if path is None:
            path = Path(self.output_dir) / "index.json"
        path.write_text(
            json.dumps(
                {
                    "pdf_path": self.pdf_path,
                    "output_dir": self.output_dir,
                    "total_pages": self.total_pages,
                    "asset_count": len(self.assets),
                    "assets": [a.to_dict() for a in self.assets],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path


@dataclass(frozen=True)
class _CaptionCandidate:
    """Internal: a detected caption candidate on a page."""

    kind: Literal["figure", "table"]
    label: str
    title: str
    pdf_page: int
    bbox: Any  # fitz.Rect, but we avoid importing fitz here for type-check speed


@dataclass
class ExtractorConfig:
    """Configuration for the chart extractor."""

    # Resolution multiplier for extracted images
    image_scale: float = 2.0

    # Max distance (points) between caption and content to consider related
    max_vertical_gap: float = 180.0

    # Minimum overlap or center distance for horizontal alignment
    max_horizontal_center_distance: float = 220.0

    # Padding around content when cropping (points)
    crop_padding: float = 12.0

    # Whether to skip likely table-of-contents pages
    skip_toc_pages: bool = True

    # Caption regex patterns: list of (kind, pattern) tuples
    # Each pattern should have named groups: label, title
    caption_patterns: list[tuple[Literal["figure", "table"], str]] | None = None

    def __post_init__(self) -> None:
        if self.caption_patterns is None:
            # Default patterns support both Chinese and English academic captions
            self.caption_patterns = [
                # Chinese: 图 1 / 图 1.1 / 图 1-1 Title
                (
                    "figure",
                    r"^(?:图|圖)\s*(?P<label>[0-9]{1,2}(?:[-.．][0-9]{1,3})?)\s*(?P<title>.*)$",
                ),
                # Chinese: 表 1 / 表 1.1 / 表 1-1 Title
                (
                    "table",
                    r"^(?:表)\s*(?P<label>[0-9]{1,2}(?:[-.．][0-9]{1,3})?)\s*(?P<title>.*)$",
                ),
                # English: Figure 1 / Figure 1.1 / Fig. 1 Title
                (
                    "figure",
                    r"(?i)^fig(?:ure)?\.?\s*(?P<label>[0-9]{1,2}(?:[-.][0-9]{1,3})?)\s*[:.)]?\s*(?P<title>.*)$",
                ),
                # English: Table 1 / Table 1.1 Title
                ("table", r"(?i)^table\.?\s*(?P<label>[0-9]{1,2}(?:[-.][0-9]{1,3})?)\s*[:.)]?\s*(?P<title>.*)$"),
            ]
