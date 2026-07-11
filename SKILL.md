---
name: pdf-chart-extraction
description: "Extract charts, figures, and tables from academic PDFs as high-resolution images with structured metadata. Supports Chinese (图/表) and English (Figure/Table) caption formats. Outputs PNG images + JSON index with page numbers, labels, titles, and bounding boxes. Use when an AI agent needs to analyze or reference the original visual content of a paper."
---

# PDF Chart Extraction Skill

Extract charts, figures, and tables from academic PDFs as high-resolution PNG images with structured metadata (JSON index).

This skill solves the problem where AI models summarizing papers can only output text, not the original visual content. It is especially useful for Chinese and English academic papers, theses, and reports.

## When to Use

Use this skill when you need to:

1. Summarize or analyze a paper PDF and reference the original charts, figures, or tables
2. Extract visual assets from research papers, theses, or reports for AI model analysis
3. Convert PDF figures and tables into standalone image files
4. Let an AI agent "see" the original charts from a PDF alongside text

## Core Capabilities

- **Figure extraction**: Detects figure captions, locates visual content, and crops high-resolution PNGs
- **Table extraction**: Detects table captions, uses PyMuPDF table finder or line-based inference, and crops table regions
- **Bilingual support**: Chinese captions (`图1.1`, `表3.1`) and English captions (`Figure 1.1`, `Table 3.1`)
- **Vector graphics handling**: Captures both embedded raster images and vector drawings via page rasterization
- **Structured output**: JSON index with page numbers, labels, titles, bounding boxes, detection methods
- **TOC page skipping**: Automatically skips table-of-contents pages to avoid false detections

## Installation

```bash
pip install -e .
```

## Quick Start

### Single PDF

```bash
# Extract all charts from a PDF
python -m pdf_chart_extraction.cli paper.pdf -o ./charts

# Extract specific pages only (1-based, comma-separated)
python -m pdf_chart_extraction.cli paper.pdf -p 10,11,12 -o ./charts

# Output JSON metadata to stdout
python -m pdf_chart_extraction.cli paper.pdf --json -q

# Via standalone script
python scripts/extract_charts.py paper.pdf -o ./charts -s 2.0
```

### Batch Processing

```bash
# Extract from all PDFs in a directory
python scripts/batch_extract.py ./papers -o ./extracted_charts

# With JSON summary output
python scripts/batch_extract.py ./papers -o ./extracted_charts --json

# Custom scale and file pattern
python scripts/batch_extract.py ./papers -o ./output -s 3.0 -p "*.pdf"
```

Batch output structure:

```
output_dir/
├── summary.json              # Global summary of all PDFs
├── paper_a/
│   ├── figures/
│   ├── tables/
│   └── index.json
├── paper_b/
│   ├── figures/
│   ├── tables/
│   └── index.json
└── ...
```

### Python API

```python
from pdf_chart_extraction import extract_charts, ChartExtractor, ExtractorConfig
from pathlib import Path

# Single PDF
result = extract_charts("paper.pdf", "./output")
print(f"Found {len(result.figures())} figures and {len(result.tables())} tables")

# With custom config
config = ExtractorConfig(
    image_scale=3.0,
    max_vertical_gap=200.0,
    skip_toc_pages=True,
)
extractor = ChartExtractor(config)
result = extractor.extract("paper.pdf", "./output", page_numbers=[10, 11, 12])
result.save_index()

# Batch: process multiple PDFs
pdf_dir = Path("./papers")
output_dir = Path("./extracted_charts")
output_dir.mkdir(parents=True, exist_ok=True)

for pdf_path in sorted(pdf_dir.glob("*.pdf")):
    pdf_output = output_dir / pdf_path.stem
    result = extractor.extract(pdf_path, pdf_output)
    print(f"{pdf_path.name}: {len(result.assets)} assets")
```

## Output Structure

```
output_dir/
├── figures/
│   ├── figure_图1.1_page_14.png
│   ├── figure_Figure_2.1_page_15.png
│   └── ...
├── tables/
│   ├── table_表3.1_page_22.png
│   ├── table_Table_4.1_page_30.png
│   └── ...
└── index.json
```

### JSON Index Format

```json
{
  "pdf_path": "paper.pdf",
  "output_dir": "./output",
  "total_pages": 58,
  "asset_count": 42,
  "assets": [
    {
      "kind": "figure",
      "label": "图1.1",
      "title": "技术路线",
      "pdf_page": 14,
      "caption_bbox": [255.6, 721.3, 339.6, 737.04],
      "content_bbox": [70.8, 398.88, 523.92, 711.12],
      "image_path": "output/figures/figure_图1.1_page_14.png",
      "caption_position": "below",
      "detection_method": "visual_region"
    }
  ]
}
```

## Detection Methods

| Method | Description | When Used |
|--------|-------------|-----------|
| `pymupdf_table` | PyMuPDF's built-in table finder | Tables with clear grid structure |
| `line_based_table` | Inferred from text line positions | Tables without clear borders |
| `visual_region` | Detected image/drawing blocks | Figures with embedded images |
| `caption_gap` | Inferred from whitespace above caption | Figures in text-heavy layouts |
| `caption_only` | No content region found | Fallback when content cannot be located |

## Configuration

`ExtractorConfig` parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `image_scale` | `2.0` | Resolution multiplier for extracted PNGs |
| `max_vertical_gap` | `180.0` | Max points between caption and content |
| `max_horizontal_center_distance` | `220.0` | Max horizontal misalignment |
| `crop_padding` | `12.0` | Padding around crop region in points |
| `skip_toc_pages` | `True` | Skip table-of-contents pages |
| `caption_patterns` | See code | Regex patterns for caption detection |

## For AI Agent Integration

When an AI agent needs to analyze a paper's charts:

1. **Run extraction**: `python scripts/extract_charts.py paper.pdf -o ./charts --json`
2. **Parse index.json**: Get metadata for all charts
3. **Feed images to vision model**: Load PNG files alongside text prompts
4. **Reference by label**: "As shown in `图3.1` (see attached image)..."

This bridges the gap between text-only PDF parsing and visual understanding.

## Repository

- GitHub: https://github.com/James-Leong/pdf-chart-extraction
- License: MIT
