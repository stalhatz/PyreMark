# PyreMark

PYthon REsume for Markdown: Multi-lingual, modular CV/cover letter generation from YAML + Jinja2 templates to HTML and PDF.

## Quick pitch

PyreMark is a document generation pipeline for multi-lingual, multi-profile professionals who need to produce tailored CVs and cover letters from a single data source. Define your experience once in YAML, compose sections declaratively, and render to pixel-perfect PDF via Jinja2 templates and Chromium.

The workflow: YAML data files are selectively assembled via a TOML configuration file, rendered through Jinja2 HTML/CSS templates, and converted to PDF using Playwright/Chromium. Cover letters can be authored as Markdown files with YAML front-matter and automatically transformed into the same pipeline. The result: one data source, many outputs — different profiles, languages, or section selections.

## What's interesting about this

- **Multi-lingualism baked in.** Every data field can be a plain string or a language indexed dictionary. A Jinja2 macro handles fallback automatically, no separate files or duplicated structures needed.
- **Modularity by design.** Data (YAML), presentation (Jinja2 templates), and configuration (TOML) are independent layers. Sections are self-contained data objects that declare their own template. Compose, reorder, or omit sections per build without touching template code.
- **Powerful configuration-driven builds**. The configuration file is the single control surface for each build — it selects which YAML data files to include, defines section order, overrides data fields at any level, and sets style tokens, all in one human-readable format. Different .toml profiles can produce entirely different CVs (different sections, emphasis, styling) from the same YAML data repository.

## What this project isn't / current concerns

- **Theming-based design** : This project does not intend to become a universal CV creator with drag-and-drop design or canvas-based editing. Finely-tunable theming is the way to go for users to get a custom appearance for their documents.
- **Data ownership**: Insisting on human-readable interfaces makes much more sense for users that want to own their data. That implies interoperability, and an open environment/exosystem for the future.
- **Bigest concern at this moment**: The YAML schema ad-hoc and, thus, not being validated. This makes it harder for a user to draft their CV without diving into the format. An ideal input path into a PyreMark project would be for an LLM to scan an existing .doc/.ppt cv and create yaml files based on some JSON Schema file.


## Similar projects

1. [Yaml Resume](https://yamlresume.dev/) — LaTeX-based rendering, which makes visual customization harder and does not support multi-lingual data natively. PyreMark uses Jinja2/HTML+CSS for full control over layout and styling.

2. [JSON Resume](https://jsonresume.org/) — Defines a schema for CV data with community-driven themes, but lacks built-in multilingual support. PyreMark handles translations at the data level, allowing a single YAML source to produce CVs in any language.

3. [ModernCV / Awesome-CV](https://github.com/posquit0/Awesome-CV) — LaTeX-based, single-language templates with limited customization. PyreMark's Jinja2 approach lets users compose, reuse, and theme sections without learning LaTeX.

## Getting Started / Quick Start

```bash
git clone https://github.com/stalhatz/PyreMark
cd PyreMark
poetry install
playwright install chromium
poetry run python ./src/main.py --cv ./testdata/cv/single_page.toml -o ./pdf/output.pdf
```

## Future features

- **JSON Schema / Pydantic validation** ([spec](./specs/features/JSON-schema.md) / [spec](./specs/features/pydantic-classes.md)) — schema validation for YAML data, integration with LLMs, automatic schema generation
- **XMP metadata** ([spec](./specs/features/xmp-metadata.md)) — embed build version, data source hash, and tags into generated PDFs
- **MCP server** ([spec](./specs/features/MCP-server.md)) — allow LLMs to interact with PyreMark data to assemble tailored CVs per job listing
- **Web app** ([spec](./specs/features/webapp.md)) — browser-based CV builder with section management, live preview, and YAML export
- **Obsidian plugin** — integrate the Markdown-to-CV workflow directly into Obsidian

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for architecture documentation, project structure, and conventions. Feature specifications live in [`specs/`](./specs/).