#!/usr/bin/env python3
"""Standalone script for AI agents to extract charts from PDFs.

Usage:
    python extract_charts.py <pdf_path> [-o <output_dir>] [-s <scale>] [-p <pages>]

Examples:
    python extract_charts.py paper.pdf
    python extract_charts.py paper.pdf -o ./charts -s 2.0
    python extract_charts.py paper.pdf -p 1,3,5-10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _parse_pages(pages_str: str | None) -> list[int] | None:
    """Parse page number string like '1,3,5-10' to list of integers."""
    try:
        from pdf_chart_extraction.cli import parse_pages
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from pdf_chart_extraction.cli import parse_pages

    return parse_pages(pages_str)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract charts, figures, and tables from academic PDFs")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("-o", "--output", default="./extracted_charts", help="Output directory")
    parser.add_argument("-s", "--scale", type=float, default=2.0, help="Image scale multiplier")
    parser.add_argument("-p", "--pages", help="Page numbers: e.g., '1,3,5-10'")
    parser.add_argument("--json", action="store_true", help="Output JSON result to stdout")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    try:
        import fitz  # noqa: F401
    except ImportError:
        print(
            "Error: PyMuPDF (fitz) not installed. Run: pip install pymupdf",
            file=sys.stderr,
        )
        return 1

    try:
        from pdf_chart_extraction import ChartExtractor, ExtractorConfig
    except ImportError:
        # Fallback: add parent to path if running script directly
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from pdf_chart_extraction import ChartExtractor, ExtractorConfig

    config = ExtractorConfig(
        image_scale=args.scale,
        skip_toc_pages=True,
    )
    extractor = ChartExtractor(config)
    page_numbers = _parse_pages(args.pages)

    result = extractor.extract(pdf_path, args.output, page_numbers=page_numbers)

    if args.json:
        print(
            json.dumps(
                {
                    "pdf_path": result.pdf_path,
                    "output_dir": result.output_dir,
                    "total_pages": result.total_pages,
                    "asset_count": len(result.assets),
                    "figures": len(result.figures()),
                    "tables": len(result.tables()),
                    "assets": [a.to_dict() for a in result.assets],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif not args.quiet:
        print(f"\nExtracted {len(result.assets)} assets from {result.total_pages} pages")
        print(f"   Output: {result.output_dir}")
        print(f"   Figures: {len(result.figures())}, Tables: {len(result.tables())}")
        for asset in result.assets:
            status = "ok" if asset.image_path else "missing"
            kind_label = "Figure" if asset.kind == "figure" else "Table"
            print(f"   [{status}] {kind_label}: {asset.label} - {asset.title} (page {asset.pdf_page})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
