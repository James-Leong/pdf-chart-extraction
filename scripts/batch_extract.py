#!/usr/bin/env python3
"""Batch extract charts from multiple PDFs in a directory.

Usage:
    python batch_extract.py <pdf_directory> [-o <output_dir>] [-s <scale>]

Examples:
    python batch_extract.py ./papers -o ./extracted_charts
    python batch_extract.py ./papers -o ./extracted_charts -s 2.0 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def batch_extract(
    pdf_dir: Path,
    output_dir: Path,
    *,
    scale: float = 2.0,
    pattern: str = "*.pdf",
    quiet: bool = False,
) -> dict:
    """Extract charts from all PDFs in a directory.

    Args:
        pdf_dir: Directory containing PDF files.
        output_dir: Root directory for extracted outputs.
        scale: Image scale multiplier.
        pattern: Glob pattern to match PDF files.
        quiet: Suppress progress output.

    Returns:
        Summary dict with results per PDF.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
        from pdf_chart_extraction import ChartExtractor, ExtractorConfig
    except ImportError:
        print("Error: pdf_chart_extraction module not found.", file=sys.stderr)
        sys.exit(1)

    pdf_files = sorted(pdf_dir.glob(pattern))
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir} matching '{pattern}'", file=sys.stderr)
        return {"total_pdfs": 0, "results": []}

    config = ExtractorConfig(image_scale=scale, skip_toc_pages=True)
    extractor = ChartExtractor(config)

    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    total_assets = 0

    for pdf_path in pdf_files:
        pdf_name = pdf_path.stem
        pdf_output = output_dir / pdf_name
        pdf_output.mkdir(parents=True, exist_ok=True)

        if not quiet:
            print(f"\nProcessing: {pdf_path.name}")

        try:
            result = extractor.extract(pdf_path, pdf_output)
            summary = {
                "pdf_name": pdf_path.name,
                "pdf_path": str(pdf_path),
                "output_dir": str(pdf_output),
                "total_pages": result.total_pages,
                "asset_count": len(result.assets),
                "figures": len(result.figures()),
                "tables": len(result.tables()),
                "status": "success",
            }
            total_assets += len(result.assets)
            if not quiet:
                print(
                    f"   ok: {len(result.assets)} assets ({len(result.figures())} figures, {len(result.tables())} tables)"
                )
        except Exception as exc:
            summary = {
                "pdf_name": pdf_path.name,
                "pdf_path": str(pdf_path),
                "output_dir": str(pdf_output),
                "status": "failed",
                "error": str(exc),
            }
            if not quiet:
                print(f"   failed: {exc}")

        results.append(summary)

    global_summary = {
        "total_pdfs": len(pdf_files),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "total_assets": total_assets,
        "output_dir": str(output_dir),
        "results": results,
    }

    # Save global summary
    summary_path = output_dir / "summary.json"
    summary_path.write_text(json.dumps(global_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if not quiet:
        print(f"\n{'=' * 50}")
        print("Batch extraction complete")
        print(f"   Total PDFs: {global_summary['total_pdfs']}")
        print(f"   Successful: {global_summary['successful']}")
        print(f"   Failed: {global_summary['failed']}")
        print(f"   Total assets: {global_summary['total_assets']}")
        print(f"   Summary: {summary_path}")

    return global_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch extract charts, figures, and tables from multiple PDFs.")
    parser.add_argument("directory", help="Directory containing PDF files")
    parser.add_argument("-o", "--output", default="./extracted_charts", help="Output directory")
    parser.add_argument("-s", "--scale", type=float, default=2.0, help="Image scale multiplier")
    parser.add_argument("-p", "--pattern", default="*.pdf", help="File glob pattern (default: *.pdf)")
    parser.add_argument("--json", action="store_true", help="Output summary JSON to stdout")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    pdf_dir = Path(args.directory)
    if not pdf_dir.exists():
        print(f"Error: Directory not found: {pdf_dir}", file=sys.stderr)
        return 1
    if not pdf_dir.is_dir():
        print(f"Error: Not a directory: {pdf_dir}", file=sys.stderr)
        return 1

    summary = batch_extract(
        pdf_dir,
        Path(args.output),
        scale=args.scale,
        pattern=args.pattern,
        quiet=args.quiet,
    )

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
