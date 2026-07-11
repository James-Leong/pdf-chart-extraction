"""Tests for pdf_chart_extraction."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure src is on path when running tests directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pdf_chart_extraction import ChartExtractor, ExtractorConfig, extract_charts
from pdf_chart_extraction.cli import parse_pages
from pdf_chart_extraction.models import ChartAsset


@pytest.fixture
def extractor() -> ChartExtractor:
    return ChartExtractor(ExtractorConfig(image_scale=1.0))


@pytest.fixture
def test_pdf() -> Path:
    path = Path(__file__).resolve().parent / "attention_is_all_you_need.pdf"
    if not path.exists():
        pytest.skip("attention_is_all_you_need.pdf not found — copy the PDF to tests/ for testing")
    return path


class TestExtractorConfig:
    def test_default_patterns(self) -> None:
        config = ExtractorConfig()
        assert config.caption_patterns is not None
        assert len(config.caption_patterns) >= 4  # Chinese + English

    def test_custom_config(self) -> None:
        config = ExtractorConfig(image_scale=3.0, max_vertical_gap=250.0)
        assert config.image_scale == 3.0
        assert config.max_vertical_gap == 250.0


class TestCliParsing:
    def test_parse_pages_supports_ranges(self) -> None:
        assert parse_pages("3,1,5-7,6") == [1, 3, 5, 6, 7]

    @pytest.mark.parametrize("pages", ["0", "2-1", "1,a"])
    def test_parse_pages_rejects_invalid_input(self, pages: str) -> None:
        with pytest.raises(ValueError):
            parse_pages(pages)


class TestChartExtractor:
    def test_extract_basic(self, extractor: ChartExtractor, test_pdf: Path, tmp_path: Path) -> None:
        result = extractor.extract(test_pdf, tmp_path)
        assert result.total_pages > 0
        assert len(result.assets) > 0
        assert all(isinstance(a, ChartAsset) for a in result.assets)

    def test_figures_and_tables_separated(self, extractor: ChartExtractor, test_pdf: Path, tmp_path: Path) -> None:
        result = extractor.extract(test_pdf, tmp_path)
        figures = result.figures()
        tables = result.tables()
        assert len(figures) + len(tables) == len(result.assets)
        assert all(a.kind == "figure" for a in figures)
        assert all(a.kind == "table" for a in tables)

    def test_asset_fields(self, extractor: ChartExtractor, test_pdf: Path, tmp_path: Path) -> None:
        result = extractor.extract(test_pdf, tmp_path)
        for asset in result.assets:
            assert asset.pdf_page >= 1
            assert asset.label
            assert asset.caption_bbox is not None
            assert len(asset.caption_bbox) == 4
            assert asset.detection_method in {
                "pymupdf_table",
                "line_based_table",
                "visual_region",
                "caption_gap",
                "caption_only",
            }

    def test_index_json_saved(self, extractor: ChartExtractor, test_pdf: Path, tmp_path: Path) -> None:
        result = extractor.extract(test_pdf, tmp_path)
        index_path = tmp_path / "index.json"
        assert index_path.exists()
        data = json.loads(index_path.read_text(encoding="utf-8"))
        assert data["pdf_path"] == str(test_pdf)
        assert data["asset_count"] == len(result.assets)
        assert len(data["assets"]) == len(result.assets)

    def test_single_page_extraction(self, extractor: ChartExtractor, test_pdf: Path, tmp_path: Path) -> None:
        result = extractor.extract(test_pdf, tmp_path, page_numbers=[3])
        # Page 3 should have Figure 1 in the Attention Is All You Need paper
        assert all(a.pdf_page == 3 for a in result.assets)
        assert any(a.kind == "figure" and a.label == "Figure 1" for a in result.assets)

    def test_output_images_exist(self, extractor: ChartExtractor, test_pdf: Path, tmp_path: Path) -> None:
        result = extractor.extract(test_pdf, tmp_path)
        for asset in result.assets:
            if asset.image_path:
                path = Path(asset.image_path)
                assert path.exists(), f"Expected image not found: {path}"
                assert path.stat().st_size > 0


class TestExtractChartsConvenience:
    def test_extract_charts_function(self, test_pdf: Path, tmp_path: Path) -> None:
        result = extract_charts(test_pdf, tmp_path)
        assert len(result.assets) > 0
        assert result.pdf_path == str(test_pdf)


class TestCaptionPatterns:
    """Test that default caption patterns match expected formats."""

    @pytest.mark.parametrize(
        "text,expected_kind,expected_label",
        [
            ("图 1.1 技术路线", "figure", "图1.1"),
            ("图3.1 M公司主要会计指标折线", "figure", "图3.1"),
            ("图1 示例图", "figure", "图1"),
            ("图 1 示例图", "figure", "图1"),
            ("图2-3 示例图", "figure", "图2-3"),
            ("表 4.1 M公司总资产收益率（%）", "table", "表4.1"),
            ("表4.2 M公司主要经营指标", "table", "表4.2"),
            ("表1 示例表", "table", "表1"),
            ("表 1 示例表", "table", "表1"),
            ("Figure 1 The Transformer", "figure", "Figure 1"),
            ("Figure 1.1 Overview", "figure", "Figure 1.1"),
            ("Fig. 2.3 Results", "figure", "Figure 2.3"),
            ("Figure 2: (left) Scaled Dot-Product Attention", "figure", "Figure 2"),
            ("Table 1 Data summary", "table", "Table 1"),
            ("TABLE 4.1 Comparison", "table", "Table 4.1"),
            ("Table 3: Variations", "table", "Table 3"),
        ],
    )
    def test_pattern_matching(self, text: str, expected_kind: str, expected_label: str) -> None:
        import re

        config = ExtractorConfig()
        matched = False
        for kind, pattern in config.caption_patterns:
            m = re.match(pattern, text)
            if m:
                assert kind == expected_kind
                matched = True
                break
        assert matched, f"No pattern matched: {text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
