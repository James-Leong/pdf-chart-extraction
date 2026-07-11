# PDF Chart Extraction

[![CI](https://github.com/James-Leong/pdf-chart-extraction/actions/workflows/ci.yml/badge.svg)](https://github.com/James-Leong/pdf-chart-extraction/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

[English](#english) | [中文](#chinese)

---

<a id="english"></a>
## English

Extract charts, figures, and tables from academic PDFs as high-resolution PNG images with structured metadata (JSON index).

This project bridges the gap between text-only PDF parsing and visual understanding: AI agents can now "see" the original charts, figures, and tables from Chinese/English papers alongside text analysis.

### Features

- **Figure extraction**: Detects figure captions and crops the corresponding visual regions
- **Table extraction**: Detects table captions and extracts table regions via PyMuPDF or line-based inference
- **Bilingual captions**: Supports Chinese (`图1.1`, `表3.1`) and English (`Figure 1.1`, `Table 3.1`) formats
- **Vector graphics**: Captures both raster images and vector drawings via page rasterization
- **Structured output**: Generates `index.json` with page numbers, labels, titles, bounding boxes, and detection methods
- **TOC skipping**: Automatically skips table-of-contents pages to reduce false detections
- **Batch processing**: Extract charts from multiple PDFs in one command

### Installation

#### Use as a Codex skill

Install the skills-only plugin from this GitHub repository:

```bash
codex plugin marketplace add James-Leong/pdf-chart-extraction
codex plugin marketplace list
```

Then open Codex or ChatGPT Desktop, go to Plugins, choose the `pdf-chart-extraction-local` marketplace, install **PDF Chart Extraction**, and start a new task.

Install the Python CLI used by the skill:

```bash
pip install "git+https://github.com/James-Leong/pdf-chart-extraction.git"
```

After that, ask Codex:

```text
Use the pdf-chart-extraction skill to extract figures and tables from paper.pdf into ./charts.
```

The skill guides Codex to run `pdf-chart-extract`, read `index.json`, and use the extracted PNG files for visual analysis.

#### Python package

```bash
# From GitHub
pip install "git+https://github.com/James-Leong/pdf-chart-extraction.git"

# From source
git clone https://github.com/James-Leong/pdf-chart-extraction.git
cd pdf-chart-extraction
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

### Quick Start

```bash
# Extract all charts from a single PDF
pdf-chart-extract paper.pdf -o ./charts

# Or via Python module
python -m pdf_chart_extraction.cli paper.pdf -o ./charts

# Extract specific pages only
pdf-chart-extract paper.pdf -p 10-30 -o ./charts

# Output JSON metadata to stdout
pdf-chart-extract paper.pdf --json -q

# Batch process a directory of PDFs
python scripts/batch_extract.py ./papers -o ./extracted_charts --json
```

### Python API

```python
from pathlib import Path
from pdf_chart_extraction import ChartExtractor, ExtractorConfig, extract_charts

# Simple usage
result = extract_charts("paper.pdf", "./output")
print(f"Found {len(result.figures())} figures and {len(result.tables())} tables")

# Custom configuration
config = ExtractorConfig(
    image_scale=3.0,
    max_vertical_gap=200.0,
    skip_toc_pages=True,
)
extractor = ChartExtractor(config)
result = extractor.extract("paper.pdf", "./output", page_numbers=[10, 11, 12])
result.save_index()
```

### Output Structure

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

See [`SKILL.md`](./SKILL.md) for detailed integration guidance for AI agents.
See [`docs/SKILL_MARKETPLACE.md`](./docs/SKILL_MARKETPLACE.md) for the skills-only plugin marketplace plan.

---

<a id="chinese"></a>
## 中文

从学术论文 PDF 中以高分辨率 PNG 图片和结构化元数据（JSON 索引）的形式提取图表、图片和表格。

本项目填补了仅文本 PDF 解析与视觉理解之间的空白：AI 智能体现在可以在文本分析的同时"看到"中英文学术论文中的原始图表内容。

### 功能特性

- **图片提取**：检测图标题并裁剪对应视觉区域
- **表格提取**：检测表标题并通过 PyMuPDF 或基于行推断的方式提取表格区域
- **双语标题**：支持中文（`图1.1`、`表3.1`）和英文（`Figure 1.1`、`Table 3.1`）格式
- **矢量图形**：通过页面栅格化捕获嵌入位图和矢量绘图
- **结构化输出**：生成包含页码、标签、标题、边界框和检测方法的 `index.json`
- **目录页跳过**：自动跳过目录页以减少误检测
- **批量处理**：一条命令从多个 PDF 中提取图表

### 安装

#### 作为 Codex skill 使用

从本 GitHub 仓库安装 skills-only plugin：

```bash
codex plugin marketplace add James-Leong/pdf-chart-extraction
codex plugin marketplace list
```

然后打开 Codex 或 ChatGPT Desktop，进入 Plugins，选择 `pdf-chart-extraction-local` marketplace，安装 **PDF Chart Extraction**，并新开一个任务。

安装该 skill 会调用的 Python CLI：

```bash
pip install "git+https://github.com/James-Leong/pdf-chart-extraction.git"
```

之后可以直接对 Codex 说：

```text
使用 pdf-chart-extraction skill，把 paper.pdf 里的图和表提取到 ./charts。
```

该 skill 会引导 Codex 运行 `pdf-chart-extract`，读取 `index.json`，并使用导出的 PNG 图片进行视觉分析。

#### Python 包

```bash
# 从 GitHub 安装
pip install "git+https://github.com/James-Leong/pdf-chart-extraction.git"

# 从源码安装
git clone https://github.com/James-Leong/pdf-chart-extraction.git
cd pdf-chart-extraction
pip install -e .

# 包含开发依赖
pip install -e ".[dev]"
```

### 快速开始

```bash
# 从单个 PDF 提取所有图表
pdf-chart-extract paper.pdf -o ./charts

# 或通过 Python 模块
python -m pdf_chart_extraction.cli paper.pdf -o ./charts

# 仅提取指定页面
pdf-chart-extract paper.pdf -p 10-30 -o ./charts

# 将 JSON 元数据输出到标准输出
pdf-chart-extract paper.pdf --json -q

# 批量处理 PDF 目录
python scripts/batch_extract.py ./papers -o ./extracted_charts --json
```

### Python API

```python
from pathlib import Path
from pdf_chart_extraction import ChartExtractor, ExtractorConfig, extract_charts

# 简单用法
result = extract_charts("paper.pdf", "./output")
print(f"发现 {len(result.figures())} 个图和 {len(result.tables())} 个表")

# 自定义配置
config = ExtractorConfig(
    image_scale=3.0,
    max_vertical_gap=200.0,
    skip_toc_pages=True,
)
extractor = ChartExtractor(config)
result = extractor.extract("paper.pdf", "./output", page_numbers=[10, 11, 12])
result.save_index()
```

### 输出结构

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

AI 智能体集成的详细指南请参见 [`SKILL.md`](./SKILL.md)。
skills-only plugin 市场分发方案请参见 [`docs/SKILL_MARKETPLACE.md`](./docs/SKILL_MARKETPLACE.md)。

---

## Development

```bash
# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Type check
mypy src

# Build package
python -m build
twine check dist/*
```

## License

[MIT](./LICENSE)
