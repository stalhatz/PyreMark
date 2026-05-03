---
status: draft
area: architecture
size: medium
depends_on: specs/testing/test-enhancement-spec.md (execution items 5–8)
---

# Split `src/build.py` into a proper Python package

## Current state

`src/build.py` is a 932-line monolith containing **every** concern in the project:

| Concern | Lines (approx.) |
|---|---|
| CLI argument parsing (`parse_cli_args`) | 36 |
| Config resolution (`resolve_build_config`, `load_toml_config`, `overlay_args`) | 138 |
| Logging setup (`setup_logging`) | 9 |
| Theme system (`ThemeResolver`, `ThemeLoader`, `copy_theme_images`) | 155 |
| YAML data loading/sorting (`readYamlData`, `sortData`, `sortDict`, `findDateField`, `yearInDateString`) | 70 |
| i18n + dict utilities (`tr`, `deep_merge`, `overlay`) | 75 |
| Template rendering (`renderTemplateAndWriteToFile`) | 27 |
| HTML/PDF viewers + PDF generation (`showHTML`, `viewPDF`, `html_to_pdf_chromium`) | 47 |
| QR code generation (`generate_qr_code`, `createQRCode`) | 42 |
| Image resolution (`resolve_user_images`, `_IMAGE_FIELDS`) | 43 |
| Entry point (`if __name__ == "__main__"` block — 105 lines of procedural orchestration) | 105 |
| Enums + dataclasses (`DocumentType`, `BuildConfig`) | 28 |
| Mid-file imports (`import asyncio`, `import re` at lines 240/338; unused `from re import compile` at line 8) | — |
| **TOTAL** | **~932** |

Additional structural issues:

- **Not a package**: `src/` has no `__init__.py`. Tests import via `sys.path.insert` hack.  
- **`pyproject.toml`** has `package-mode = false` — the project is configured as a script, not an installable package.
- **Stale dependencies**: `jinja2-cli` and `hiyapyco` are listed but only `jinja2` (the library) is actually used.
- **Import disorder**: standard library, third-party, and local imports are intermixed. Mid-file imports exist at lines 240 and 338.
- **No `main()` function**: the 105-line `__main__` guard is untestable procedural code.

All of this makes adding any feature (schema validation, XMP metadata, MCP server, template-based CSS encapsulation) painful — everything gets bolted onto an already-overstuffed file.

---

## Target state

A proper Python package under `src/` with modules organized by concern:

```
src/
├── __init__.py          # empty (makes src/ a package)
├── config.py            # CLI + build configuration (~200 lines)
├── theme.py             # ThemeResolver, ThemeLoader, copy_theme_images (~160 lines)
├── data.py              # YAML reading, merging, sorting, i18n (~170 lines)
├── rendering.py         # Jinja2 + PDF + viewers (~90 lines)
├── images.py            # QR codes + user image resolution (~90 lines)
└── main.py              # main() entry point + __main__ guard (~110 lines)
```

### Module responsibilities

#### `src/config.py`
- `DocumentType` (str, Enum)
- `BuildConfig` (dataclass)
- `parse_cli_args() → argparse.Namespace`
- `load_toml_config(path: str) → dict`
- `overlay_args(toml_config: dict, cli_args_dict: dict) → SimpleNamespace`
- `resolve_build_config(args, yaml_files, config_file_path) → BuildConfig`
- `setup_logging(verbose: str) → None`

#### `src/theme.py`
- `ThemeLoader(BaseLoader)` — Jinja2 template loader with search paths
- `ThemeResolver` — theme path resolution, manifest parsing, extend chain, image search paths, pre/post styles
- `copy_theme_images(image_paths, output_img_dir) → None`

#### `src/data.py`
- `deep_merge(d1, d2, replace=False) → Any`
- `overlay(base, top) → dict` — shallow config overlay
- `tr(prop, lang=None, default=None) → Any` — i18n property resolver
- `readYamlData(yamlFiles) → dict`
- `yearInDateString(s) → str | None`
- `findDateField(x) → int | None`
- `sortDict(lines, dsc, key) → dict`
- `sortData(data, dsc=False) → None` — in-place date-sorting of `"lines"` dicts
- `load_and_merge_data(yaml_files, data_override) → dict`
- `prepare_data(data, lang) → dict`

#### `src/rendering.py`
- `renderTemplateAndWriteToFile(template_filename, data, output_filename, search_paths) → None`
- `showHTML(htmlFile) → None`
- `viewPDF(pdfFile) → None`
- `html_to_pdf_chromium(html_path, output_path) → None` (async)

#### `src/images.py`
- `generate_qr_code(url, output_path) → None`
- `createQRCode(data, lang, path) → None`
- `resolve_user_images(data, data_root, img_dir) → None`
- `_IMAGE_FIELDS` (module-level constant)

#### `src/main.py`
- `main() → None` — the extracted orchestration from the current `__main__` block
- `if __name__ == "__main__": main()` guard

The existing `src/transform_md_to_yaml_html.py` stays as-is (it's already its own module).

### Import graph (no cycles)

```
main.py → config.py, theme.py, data.py, rendering.py, images.py
                ↑           ↑         ↑             ↑
                │           │         │             │
                └───────────┴──── theme.py ─────────┘
                             │    (rendering imports ThemeLoader)
                             │
                      data.py (no internal deps)
```

- `config.py` — zero internal dependencies (only stdlib + third-party)
- `theme.py` — zero internal dependencies (only stdlib + `jinja2`)
- `data.py` — zero internal dependencies (only stdlib + `yaml`)
- `rendering.py` — depends on `theme.py` (for `ThemeLoader`), `data.py` possibly for context
- `images.py` — depends on `data.py` (for `tr`)
- `main.py` — depends on all of the above (orchestrator)

### `pyproject.toml` changes

- Set `package-mode = true`
- Add `[tool.poetry.packages]` pointing to `src/`
- Remove unused dependencies: `jinja2-cli`, `hiyapyco`
- Add `jinja2` as a direct dependency (it's already used via import)
- Ensure `pytest` is a dev dependency, not a runtime one (currently listed under `[tool.poetry.dependencies]`)

### Entry point

Add a `[tool.poetry.scripts]` entry so `pyremark` can be invoked as a CLI command:
```toml
[tool.poetry.scripts]
pyremark = "src.main:main"
```

The existing invocation (`python src/build.py --cv ...`) should remain possible via `python -m src.main --cv ...` after the split.

---

## Constraints / non-goals

- **No logic changes**. This is a pure structural refactoring — move code, fix imports, don't change behaviour.
- **Keep function signatures identical**. Tests must pass without modification (except import paths).
- **No new features**. Schema validation, XMP metadata, Phase 3 CSS belong in separate specs.
- **Coordinate with test spec**. The missing unit tests (execution items 5–8 in `specs/testing/test-enhancement-spec.md`) should be written **before** the module split, so the refactoring is validated by tests rather than done blind.

---

## Execution order

### Prerequisites
1. Complete execution items 5–8 from `specs/testing/test-enhancement-spec.md`:
   - Create `tests/conftest.py` with fixtures (`tmp_yaml_file`, `tmp_jinja2_template`, `sample_data_dict`)
   - Write unit tests for: `deep_merge`, `tr`, `overlay`, `readYamlData`, `renderTemplateAndWriteToFile`, `generate_qr_code`, `createQRCode`
   - Refactor `createQRCode` signature (`path` → `img_dir` parameter)
   - Extract `transform_md_to_yaml` core function from `transform_md_to_yaml_html.py`
   - Ensure all tests pass

### Phase 1: Package scaffolding
2. Create `src/__init__.py` (empty)
3. Update `pyproject.toml`:
   - Set `package-mode = true`
   - Add `[tool.poetry.packages]` with `include = "src"`
   - Add `[tool.poetry.scripts]` with `pyremark = "src.main:main"`
   - Remove `jinja2-cli`, `hiyapyco` from dependencies
   - Add `jinja2` to dependencies
   - Move `pytest` to `[tool.poetry.group.dev.dependencies]`

### Phase 2: Module extraction (one commit per module, in dependency order)
4. Extract `src/config.py` — move all CLI + config items from `build.py`
5. Extract `src/data.py` — move all data/i18n/utilities
6. Extract `src/theme.py` — move ThemeResolver, ThemeLoader, copy_theme_images
7. Extract `src/rendering.py` — move template rendering, PDF, viewers
8. Extract `src/images.py` — move QR generation, user image resolution
9. Create `src/main.py` — move the `__main__` block and wrap it as `main()`
10. Delete `src/build.py` (or keep as a deprecated re-export for backward compatibility)

### Phase 3: Cleanup
11. Fix test imports: replace `sys.path.insert` with proper package imports (e.g., `from src.config import BuildConfig`)
12. Run full test suite — all existing tests must pass
13. Run a manual integration test (`python -m src.main --cv testdata/cv/single_page.toml ...`)
14. Clean up stale references in `CONTRIBUTING.md` (remove `/j2` folder reference, update file structure table)

---

## What success looks like

- `src/` is a proper Python package with 7 modules (including `__init__.py` and `transform_md_to_yaml_html.py`)
- No module exceeds ~200 lines
- All existing tests pass without modification (import paths updated)
- `python -m src.main --cv testdata/cv/single_page.toml --output out.pdf` produces identical output to the current `python src/build.py ...`
- `pyproject.toml` correctly declares a package with a CLI entry point
- Stale dependencies removed; correct ones declared
- No mid-file imports; all imports at module top, grouped stdlib → third-party → internal
- `CONTRIBUTING.md` file structure table no longer references `/j2`
