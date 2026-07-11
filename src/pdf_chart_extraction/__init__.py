"""PDF Chart Extraction - Extract charts, figures, and tables from academic PDFs."""

from pdf_chart_extraction.extractor import ChartExtractor, extract_charts
from pdf_chart_extraction.models import ChartAsset, ExtractionResult, ExtractorConfig

__all__ = [
    "ChartExtractor",
    "extract_charts",
    "ChartAsset",
    "ExtractorConfig",
    "ExtractionResult",
]

__version__ = "0.1.0"
