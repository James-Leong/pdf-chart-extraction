# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of PDF Chart Extraction
- Extract figures and tables from academic PDFs as high-resolution PNG images
- Bilingual caption support for Chinese (`图`, `表`) and English (`Figure`, `Table`)
- Structured JSON index with page numbers, labels, titles, and bounding boxes
- CLI tool `pdf-chart-extract` and batch processing script
- Python API via `ChartExtractor` and `extract_charts`
- TOC page skipping to reduce false detections
- Pytest test suite with caption pattern tests
