---
size: small
---

# Extend and improve structure of Markdown interface to include CV creation

## Current state
- `transform_md_to_yaml_html.py` only supports creating cover letters.
- Document type is hard-coded to cover letter when `--md` is used.
- No support for using or extending a pre-existing configuration from a markdown note.

## Target state

### Interface

```
pyremark --md note.md [any CLI flags]
```

- `--md` and other CLI flags are **composable** — no exclusivity exception.
- Other invocation methods (`--cv`, `--yaml`) remain as lower-level primitives for scripting/testing/CI.

### Frontmatter structure

```yaml
---
extends: /absolute/path/to/config.toml
config:
  lang: fr
  output: CV_ACME.pdf
  layout:
    sections: [details, experience, qrcode]
data:
  sender:
    name: Alex
---

Body text...
```

- `extends:` — absolute path to a TOML build configuration (required).
- `config:` — overrides `BuildConfig` fields (lang, output, template, layout, theme, etc.).
- `data:` — overrides the data tree (deep-merged on top of YAML files referenced by the TOML).
- **Body** — meaningful for cover letters (becomes `text` paragraphs); **ignored when the document type is CV**.
- Document type is determined by the referenced TOML's `type` field, not hard-coded.

### Path rules

- `extends:` value **must be an absolute path** (relative paths raise an error with a clear message).
- All other paths referenced in the markdown frontmatter must also be absolute. No relative path resolution from the markdown file's directory is supported in this version.
- Paths inside the referenced TOML config (e.g., `yaml = [...]`) continue to resolve relative to the config's own directory (unchanged behaviour).
- (Note) this evidently limits the ability of the markdown frontmatter to configure in comparison to the .toml file. This is intentional. If different .yaml files are to be included, then a different .toml file should be targetted (which would naturally correspond to a different profile). Markdown frontmatter customization is mostly intended for quick configurational or textual changes (custom pitch per cv for example).

### Override priority chain (low → high)

1. Theme defaults / built-in
2. YAML data files (listed in TOML config)
3. TOML config file
4. markdown frontmatter
5. CLI flags

### Merge semantics

- **`config:` → TOML config → CLI**: shallow merge via `overlay()` (consistent with existing CLI-over-TOML behaviour). A key in a higher-priority layer replaces the entire value for that key; there is no deep-merge of nested config structs.
- **`data:` → YAML data files**: deep-merge via `deep_merge()` (consistent with existing YAML merge behaviour). Higher-priority values override or bundle with lower-priority ones.

### Architectural changes needed

1. **Frontmatter parsing** — `split_frontmatter_body()` already returns metadata as a flat dict. For the namespaced format (`config:`, `data:`), the metadata dict must be interpreted accordingly. If a top-level key is `config` or `data`, its value is routed to the corresponding pipeline; unknown top-level keys could be treated as data or rejected (TBD per implementation).

2. **Config loading from `extends:`** — When `extends:` is present in frontmatter, `main.py` should:
   - Load the TOML config (same path as `--cv` uses).
   - Overlay the frontmatter `config:` block on top of it using `overlay()`.
   - Pass the resulting namespace to `resolve_build_config()` with `config_file_path` set to the TOML path (so `data_root` resolves relative to the config directory).

3. **Data override at the right level** — The `data:` block and the body-derived YAML must be inserted into the data merge chain **after** the config's YAML files but **before** CLI-level `data_override`. Currently `transform_md_to_yaml_html` only writes a temp YAML file. The `data:` block should be deep-merged separately at the appropriate priority tier.

4. **Body handling for CVs** — When the document type (resolved from config) is CV, the markdown body is discarded (no warning in this version — simply not written into the temporary YAML). Future versions may use the body as an LLM prompt.

## UX goal

The user can customize the CV they intend to send to a job listing by writing a markdown note that:
- References a reusable base configuration.
- Overrides configuration and data inline.
- Keeps the full record of what was sent in a single markdown file.

This streamlines the application process and maintains full traceability in markdown.

## Missing pieces / Future extensions

### LLM-driven customisation (spec tbd — separate spec)
The markdown body could contain a copy of the job listing. A future flag (`--llm`) could trigger an LLM to:
- Select/adjust which sections to include.
- Rewrite content (experience bullets, summary) to match the listing.
- Output a customized CV while keeping the original data intact.

This is a separate feature with its own mechanism, captured it in a dedicated spec.

### Reproducibility
- Although PyreMark does not impose such a constraint, if userdata is tracked in a git repo, it would be nice to store the hash of the node that produced the document.
  - Implementing a mechanism that uses the specified hash could reproduce the exact same document if needed.
  - When the hash is deleted from metadata, fall back to HEAD.

### PDF Metadata / Document tracing
- If XMP metadata could be embedded in the resulting PDF (cf. [`xmp-metadata` spec](../features/xmp-metadata.md)), we could embed the PyreMark repo hash and the userdata repo hash, giving the user the ability to trace produced documents back to the code and data that generated them.
