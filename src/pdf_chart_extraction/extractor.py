"""Core chart extraction engine for academic PDFs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import fitz

from pdf_chart_extraction.models import (
    ChartAsset,
    ExtractionResult,
    ExtractorConfig,
    _CaptionCandidate,
)
from pdf_chart_extraction.utils import (
    build_crop_bbox,
    format_bbox,
    looks_like_toc_line,
    pad_rect,
    safe_filename,
    union_rects,
)


class ChartExtractor:
    """Extract charts, figures, and tables from academic PDFs."""

    def __init__(self, config: ExtractorConfig | None = None) -> None:
        self.config = config or ExtractorConfig()

    def extract(
        self,
        pdf_path: Path | str,
        output_dir: Path | str,
        *,
        page_numbers: list[int] | None = None,
    ) -> ExtractionResult:
        """Extract all chart/figure/table assets from a PDF.

        Args:
            pdf_path: Path to the PDF file.
            output_dir: Directory to save extracted images and index.
            page_numbers: Optional list of specific 1-based page numbers to process.
                          If None, all pages are processed.

        Returns:
            ExtractionResult with all detected assets.
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        figures_dir = output_dir / "figures"
        tables_dir = output_dir / "tables"
        figures_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)

        self._clear_dir(figures_dir, "figure")
        self._clear_dir(tables_dir, "table")

        assets: list[ChartAsset] = []
        doc = fitz.open(str(pdf_path))
        try:
            total_pages = len(doc)
            pages_to_process = page_numbers if page_numbers else list(range(1, total_pages + 1))

            for page_num in pages_to_process:
                if page_num < 1 or page_num > total_pages:
                    continue
                page = doc.load_page(page_num - 1)
                if self.config.skip_toc_pages and self._is_likely_toc_page(page):
                    continue

                page_assets = self._extract_page_assets(page, page_num, figures_dir, tables_dir)
                assets.extend(page_assets)
        finally:
            doc.close()

        result = ExtractionResult(
            pdf_path=str(pdf_path),
            output_dir=str(output_dir),
            assets=assets,
            total_pages=total_pages,
        )
        result.save_index()
        return result

    def extract_single_page(
        self,
        pdf_path: Path | str,
        page_number: int,
        output_dir: Path | str,
    ) -> list[ChartAsset]:
        """Extract assets from a single page."""
        result = self.extract(pdf_path, output_dir, page_numbers=[page_number])
        return result.assets

    def _extract_page_assets(
        self,
        page: fitz.Page,
        page_num: int,
        figures_dir: Path,
        tables_dir: Path,
    ) -> list[ChartAsset]:
        """Extract all assets from a single page."""
        captions = self._extract_caption_candidates(page, page_num)
        table_regions = self._extract_table_regions(page)
        visual_regions = self._extract_visual_regions(page)

        assets: list[ChartAsset] = []
        for caption in captions:
            content_bbox, method = self._match_content_bbox(caption, page, table_regions, visual_regions)
            image_path: str | None = None
            if content_bbox is not None:
                crop_bbox = build_crop_bbox(caption.bbox, content_bbox, page.rect, self.config.crop_padding)
                target_dir = figures_dir if caption.kind == "figure" else tables_dir
                filename = self._asset_filename(caption)
                image_path = str(target_dir / filename)
                self._save_page_crop(page, crop_bbox, Path(image_path))

            assets.append(
                ChartAsset(
                    kind=caption.kind,
                    label=caption.label,
                    title=caption.title,
                    pdf_page=caption.pdf_page,
                    caption_bbox=format_bbox(caption.bbox) or (0.0, 0.0, 0.0, 0.0),
                    content_bbox=format_bbox(content_bbox),
                    image_path=image_path,
                    caption_position=self._caption_position(caption.bbox, content_bbox),
                    detection_method=method,
                )
            )
        return assets

    def _extract_caption_candidates(self, page: fitz.Page, pdf_page: int) -> list[_CaptionCandidate]:
        """Detect caption candidates on a page using configured regex patterns."""
        candidates: list[_CaptionCandidate] = []
        text_dict = page.get_text("dict")

        caption_patterns = self.config.caption_patterns or []
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                if looks_like_toc_line(line_text):
                    continue

                for kind, pattern in caption_patterns:
                    match = re.match(pattern, line_text)
                    if match:
                        label = match.group("label")
                        title = match.group("title")
                        # Normalize label to consistent format
                        label = self._normalize_label(kind, label, line_text)
                        bbox = fitz.Rect(line.get("bbox"))
                        candidates.append(
                            _CaptionCandidate(
                                kind=kind,
                                label=label,
                                title=title.strip(),
                                pdf_page=pdf_page,
                                bbox=bbox,
                            )
                        )
                        break  # Only match first pattern
        return candidates

    def _normalize_label(self, kind: str, raw_label: str, original_text: str) -> str:
        """Normalize a caption label to consistent format."""
        # Replace Chinese dot with regular dot
        label = raw_label.replace("．", ".")
        # If already has kind prefix in text, use it
        if original_text.startswith("图") or original_text.startswith("圖"):
            return f"图{label}"
        if original_text.startswith("表"):
            return f"表{label}"
        if original_text.lower().startswith("fig"):
            return f"Figure {label}"
        if original_text.lower().startswith("table"):
            return f"Table {label}"
        return f"{kind}_{label}"

    def _is_likely_toc_page(self, page: fitz.Page) -> bool:
        """Check if page is likely a table of contents."""
        text = page.get_text("text")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return False
        if any(
            line in {"目录", "图目录", "表目录", "Contents", "List of Figures", "List of Tables"} for line in lines[:6]
        ):
            return True
        return sum(1 for line in lines if looks_like_toc_line(line)) >= 3

    def _extract_table_regions(self, page: fitz.Page) -> list[fitz.Rect]:
        """Extract table regions using PyMuPDF's table finder."""
        regions: list[fitz.Rect] = []
        try:
            tables = page.find_tables()
        except Exception:
            return regions
        for table in getattr(tables, "tables", []):
            bbox = getattr(table, "bbox", None)
            if bbox:
                regions.append(fitz.Rect(bbox))
        return regions

    def _extract_visual_regions(self, page: fitz.Page) -> list[fitz.Rect]:
        """Extract visual content regions (images, drawings)."""
        regions: list[fitz.Rect] = []

        # Image blocks from text dict
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") == 1:
                regions.append(fitz.Rect(block.get("bbox")))

        # Drawing paths (vector graphics)
        drawing_rects: list[fitz.Rect] = []
        try:
            drawings = page.get_drawings()
        except Exception:
            drawings = []
        for drawing in drawings:
            rect = drawing.get("rect")
            if rect is None:
                continue
            candidate = fitz.Rect(rect)
            if candidate.width >= 40 and candidate.height >= 20:
                drawing_rects.append(candidate)
        regions.extend(self._merge_nearby_rects(drawing_rects))

        return self._filter_content_regions(regions, page.rect)

    def _match_content_bbox(
        self,
        caption: _CaptionCandidate,
        page: fitz.Page,
        table_regions: list[fitz.Rect],
        visual_regions: list[fitz.Rect],
    ) -> tuple[fitz.Rect | None, str]:
        """Find the best content bbox for a caption."""
        if caption.kind == "table":
            region = self._nearest_region(caption.bbox, table_regions, prefer="below")
            if region is not None:
                return region, "pymupdf_table"
            region = self._infer_table_region_from_lines(caption.bbox, page)
            if region is not None:
                return region, "line_based_table"
            return None, "caption_only"

        # Figure: prefer visual region above caption
        region = self._nearest_region(caption.bbox, visual_regions, prefer="above")
        if region is not None:
            return region, "visual_region"
        region = self._infer_figure_region_from_caption(caption.bbox, page)
        if region is not None:
            return region, "caption_gap"
        return None, "caption_only"

    def _nearest_region(
        self,
        caption_bbox: fitz.Rect,
        regions: list[fitz.Rect],
        *,
        prefer: Literal["above", "below"],
    ) -> fitz.Rect | None:
        """Find the nearest region to a caption."""
        candidates: list[tuple[float, fitz.Rect]] = []
        caption_center_x = (caption_bbox.x0 + caption_bbox.x1) / 2
        for region in regions:
            horizontal_overlap = min(caption_bbox.x1, region.x1) - max(caption_bbox.x0, region.x0)
            center_distance = abs(((region.x0 + region.x1) / 2) - caption_center_x)
            distance = caption_bbox.y0 - region.y1 if prefer == "above" else region.y0 - caption_bbox.y1
            if distance < -8 or distance > self.config.max_vertical_gap:
                continue
            if horizontal_overlap < -20 and center_distance > self.config.max_horizontal_center_distance:
                continue
            candidates.append((abs(distance) + center_distance * 0.05, region))
        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _infer_table_region_from_lines(self, caption_bbox: fitz.Rect, page: fitz.Page) -> fitz.Rect | None:
        """Infer table region from text lines below caption."""
        footer_cutoff = page.rect.y0 + page.rect.height * 0.93
        words = page.get_text("words")
        below_words = [
            fitz.Rect(word[:4])
            for word in words
            if caption_bbox.y1 <= word[1] <= min(footer_cutoff, caption_bbox.y1 + 220)
        ]
        if len(below_words) < 6:
            return None
        return pad_rect(union_rects(below_words), page.rect, 4)

    def _infer_figure_region_from_caption(self, caption_bbox: fitz.Rect, page: fitz.Page) -> fitz.Rect | None:
        """Infer figure region from text/space above caption."""
        words = page.get_text("words")
        above_words = [
            fitz.Rect(word[:4])
            for word in words
            if max(page.rect.y0, caption_bbox.y0 - 360) <= word[3] <= caption_bbox.y0 - 8
        ]
        if len(above_words) < 3:
            return None
        region = union_rects(above_words)
        if region.height < 40:
            return None
        return pad_rect(region, page.rect, 8)

    def _merge_nearby_rects(self, rects: list[fitz.Rect]) -> list[fitz.Rect]:
        """Merge overlapping or nearby rects."""
        merged: list[fitz.Rect] = []
        for rect in sorted(rects, key=lambda item: (item.y0, item.x0)):
            matched = False
            for index, existing in enumerate(merged):
                expanded = pad_rect(existing, fitz.Rect(-10000, -10000, 10000, 10000), 20)
                if expanded.intersects(rect):
                    merged[index] = _union_rect(existing, rect)
                    matched = True
                    break
            if not matched:
                merged.append(rect)
        return merged

    def _filter_content_regions(self, regions: list[fitz.Rect], page_rect: fitz.Rect) -> list[fitz.Rect]:
        """Filter out noise regions."""
        filtered: list[fitz.Rect] = []
        for region in regions:
            if region.width < 50 or region.height < 30:
                continue
            if region.width > page_rect.width * 0.98 and region.height < 25:
                continue
            filtered.append(region)
        return filtered

    def _caption_position(
        self, caption_bbox: fitz.Rect, content_bbox: fitz.Rect | None
    ) -> Literal["above", "below", "overlap", "unknown"]:
        """Determine relative position of caption to content."""
        if content_bbox is None:
            return "unknown"
        if caption_bbox.y1 <= content_bbox.y0:
            return "above"
        if caption_bbox.y0 >= content_bbox.y1:
            return "below"
        return "overlap"

    def _save_page_crop(self, page: fitz.Page, bbox: fitz.Rect, image_path: Path) -> None:
        """Save a cropped region of a page as PNG."""
        pix = page.get_pixmap(
            matrix=fitz.Matrix(self.config.image_scale, self.config.image_scale),
            clip=bbox,
            alpha=False,
        )
        pix.save(str(image_path))

    def _asset_filename(self, caption: _CaptionCandidate) -> str:
        """Generate a safe filename for an asset image."""
        safe_label = safe_filename(caption.label)
        return f"{caption.kind}_{safe_label}_page_{caption.pdf_page}.png"

    def _clear_dir(self, directory: Path, prefix: str) -> None:
        """Clear previous extraction files."""
        for path in directory.glob(f"{prefix}_*_page_*.png"):
            path.unlink()


def _union_rect(a: fitz.Rect, b: fitz.Rect) -> fitz.Rect:
    """Union two rects."""
    result = fitz.Rect(a)
    result.include_rect(b)
    return result


def extract_charts(
    pdf_path: str | Path,
    output_dir: str | Path,
    **kwargs: Any,
) -> ExtractionResult:
    """Convenience function: extract charts from a PDF.

    Args:
        pdf_path: Path to the PDF file.
        output_dir: Directory to save extracted images.
        **kwargs: Passed to ExtractorConfig.

    Returns:
        ExtractionResult with all detected assets.
    """
    config = ExtractorConfig(**kwargs)
    extractor = ChartExtractor(config)
    return extractor.extract(pdf_path, output_dir)
