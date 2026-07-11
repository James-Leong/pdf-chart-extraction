"""Command-line interface for pdf-chart-extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pdf_chart_extraction.extractor import ChartExtractor
from pdf_chart_extraction.models import ExtractorConfig


def parse_pages(pages: str | None) -> list[int] | None:
    """Parse page numbers such as '1,3,5-8' into a sorted unique list."""
    if not pages:
        return None

    page_numbers: set[int] = set()
    for raw_part in pages.split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text.strip())
            end = int(end_text.strip())
            if start < 1 or end < start:
                raise ValueError(f"Invalid page range: {part}")
            page_numbers.update(range(start, end + 1))
        else:
            page_number = int(part)
            if page_number < 1:
                raise ValueError(f"Invalid page number: {part}")
            page_numbers.add(page_number)

    return sorted(page_numbers)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract charts, figures, and tables from academic PDFs.")
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("-o", "--output", default="./extracted_charts", help="Output directory")
    parser.add_argument("-s", "--scale", type=float, default=2.0, help="Image scale multiplier")
    parser.add_argument("-p", "--pages", help="Page numbers: e.g. '1,3,5-10'")
    parser.add_argument("--skip-toc", action="store_true", default=True, help="Skip table of contents pages")
    parser.add_argument("--no-skip-toc", action="store_false", dest="skip_toc", help="Don't skip TOC pages")
    parser.add_argument("--json", action="store_true", help="Output result as JSON to stdout")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error output")

    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1

    page_numbers = None
    if args.pages:
        try:
            page_numbers = parse_pages(args.pages)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    config = ExtractorConfig(
        image_scale=args.scale,
        skip_toc_pages=args.skip_toc,
    )
    extractor = ChartExtractor(config)

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
            print(f"   [{status}] {asset.kind}: {asset.label} - {asset.title} (page {asset.pdf_page})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
