# PyreMark

**v0.2.0** — A document generation pipeline for multi-lingual, multi-profile professionals who need to produce **tailored CVs and cover letters** from a portable, self-owned data repository.

<br>

<div align="center"> 

***Define your career data once. Compose targeted outputs.***

</div>

<br>

## Overview

PyreMark turns a single repository of YAML data into many tailored documents. Select different sections, reorder them, switch languages, or apply different themes — all from the same source data, controlled by a TOML configuration file.

## Workflow

| Layer | Format | Purpose |
|-------|--------|---------|
| Data | YAML | Capture experience, skills, education as independent modules |
| Config | TOML | Select files, set language, reorder sections, override fields |
| Template | Jinja2 + HTML/CSS | Rendering via headless Chromium |

**YAML data modules** are selectively assembled via a **TOML configuration file**, rendered through **Jinja2 HTML/CSS templates**, and converted to **PDF using Playwright/Chromium**. Cover letters can be authored as Markdown files with YAML front-matter and automatically fed into the same pipeline.

## Features

- **Multi-lingual data.** Every field can be a plain string or a language-indexed dictionary. Built-in fallback — no duplicate files needed.

- **Modular by design.** Sections are self-contained data objects that declare their own template. Compose, reorder, or omit sections per build without touching template code.

- **Configuration-driven.** A single TOML file controls which data to include, section order, field overrides, and style tokens. Different profiles produce entirely different documents from the same YAML repository.

- **Theme system.** Named themes provide templates, styles, and images. Themes can extend other themes, and users can override any template with a local theme directory. Pre/post CSS files allow fine-tuning without forking.

- **QR codes.** Sections can automatically generate QR code images from a URL field, embedded directly in the output.

- **XMP metadata.** Generated PDFs carry embedded metadata allowing for traceability and reproducibility

- **Markdown workflow.** Write cover letters in Markdown with PyreMark front-matter. The body becomes document content, front-matter provides metadata, and a referenced TOML config handles the build.

- **Data export.** Export the merged data or full build dictionary to YAML for debugging or external use.

## What this project does not plan to become

- **Drag and drop/ WYSIWYG**: This project does not intend to become a universal CV creator with canvas-based editing. Finely-tunable theming is the way to go for users to get a personalized appearance for their documents.
- **Data ownership**: Insisting on human-readable interfaces makes much more sense for users that want to own their data. That implies interoperability, and an open environment/ecosystem for the future.

## Similar projects

1. [Yaml Resume](https://yamlresume.dev/) — LaTeX-based, harder to customize visually, no native multi-lingual support.

2. [JSON Resume](https://jsonresume.org/) — Schema-driven with community themes, but no built-in multilingual support.

3. [ModernCV / Awesome-CV](https://github.com/posquit0/Awesome-CV) — LaTeX-based, single-language. PyreMark's Jinja2 approach requires no LaTeX knowledge.

## Getting Started

### Prerequisites

- Python 3.12+
- [Poetry](https://python-poetry.org/)

### Installation

```bash
git clone https://github.com/stalhatz/PyreMark
cd PyreMark
poetry install
poetry run playwright install chromium
```

### Quick Start

Generate a CV from a TOML configuration:

```bash
poetry run pyremark --cv testdata/cv/single_page.toml -o output.pdf
```

Generate a cover letter from Markdown:

```bash
poetry run pyremark -m testdata/md/cover_letter.md -o cover_letter.pdf
```

Preview the HTML before generating PDF:

```bash
poetry run pyremark --cv testdata/cv/single_page.toml -s html
```

### Key CLI Flags

| Flag | Description |
|------|-------------|
| `--cv <file>` | TOML configuration file |
| `-m, --md <file>` | Markdown file with front-matter |
| `-l, --lang <code>` | Output language (default: `en`) |
| `-o, --output <file>` | Output PDF path |
| `-s, --show <pdf\|html\|None>` | Preview output |
| `--theme <name>` | Named theme |
| `--tags <tag>` | Document tags for PDF metadata (repeatable) |

Run `poetry run pyremark --help` for the full list of options.

## Future Features

- JSON Schema / Pydantic validation for YAML data
- MCP server for LLM-assisted CV assembly
- Web app with live preview and section management
- Obsidian plugin for Markdown-to-CV workflow

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for architecture, conventions, and development workflow.
