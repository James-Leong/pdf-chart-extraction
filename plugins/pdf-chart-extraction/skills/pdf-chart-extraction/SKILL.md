---
name: pdf-chart-extraction
description: Extract charts, figures, and tables from academic PDFs as high-resolution PNG images with structured metadata. Use when an AI agent needs original visual content from Chinese or English papers.
---

# PDF Chart Extraction

Use this skill when a user needs to extract figures, charts, or tables from a PDF paper, thesis, or report so the visual assets can be analyzed by an AI agent.

## Workflow

1. Confirm the PDF path and desired output directory.
2. Install the Python package if needed:

   ```bash
   pip install "git+https://github.com/James-Leong/pdf-chart-extraction.git"
   ```

3. Extract assets:

   ```bash
   pdf-chart-extract paper.pdf -o ./charts
   ```

4. For selected pages, use page ranges:

   ```bash
   pdf-chart-extract paper.pdf -p 10-30 -o ./charts
   ```

5. Read `index.json` from the output directory and use the listed PNG paths when asking a vision model to inspect the original charts.

## Notes

- Captions are detected for Chinese `图` and `表`, plus English `Figure`, `Fig.`, and `Table`.
- Output contains `figures/`, `tables/`, and `index.json`.
- If no assets are found, report that result plainly and suggest checking page ranges, caption style, or PDF rendering quality.
