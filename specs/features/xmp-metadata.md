---
size: medium
modified_date: 2026-05-16
implemented_git_tag: specs/features/xmp-metadata/implemented
---

# XMP Metadata Embedding

**Goal**: Embed traceability and reproducibility metadata into generated PDFs. The author should be able to answer: when was this created, using which version of the data, and using which version of the software?

## Requirements

### 1. XMP Metadata Standards

All generated PDFs shall contain XMP metadata (ISO 16684) using only standard namespaces. No custom namespaces shall be defined.

### 2. Metadata Fields

| Field | Namespace | Type | Description |
|-------|-----------|------|-------------|
| `dc:subject` | Dublin Core | Bag | Document tags for categorization |
| `xmp:CreatorTool` | XMP | Text | Software name, version, and git hash |
| `xmp:CreateDate` | XMP | Date | PDF generation timestamp |
| `xmp:ModifyDate` | XMP | Date | PDF generation timestamp |
| `xmp:MetadataDate` | XMP | Date | PDF generation timestamp |
| `xmpMM:DocumentID` | XMP Media Management | URI | Reproducible fingerprint of input data |
| `xmpMM:VersionID` | XMP Media Management | Text | Git commit hash of the data source |

### 3. Tags

- Tags are sourced from `data.tags` in the merged data dictionary
- Override hierarchy: YAML (base) → TOML → CLI `--tags` (highest priority)
- Stored as an unordered bag in `dc:subject`
- If no tags are provided, the field is omitted

### 4. Document ID

- Computed as a SHA-256 hash of the final merged data dictionary
- Provides a reproducible fingerprint: same inputs produce the same ID
- Always present in generated PDFs

### 5. Data Repository Version

- The git commit hash of the `data_root` directory
- Links the PDF to the exact state of the source data
- **If `data_root` is not a git repository**: log a warning and omit this field. PDF generation continues normally.

### 6. Software Version

- Format: `"PyreMark {version} ({git_hash})"`
- Version and git hash from the PyreMark installation
- If PyreMark is not in a git repository, format is `"PyreMark {version}"`

### 7. Configuration

- CLI flag `--tags` accepts multiple values: `--tags cv --tags engineering`
- Tags can also be defined in YAML (`data.tags`) or TOML config
- CLI overrides TOML, which overrides YAML

## Acceptance Criteria

- [ ] PDFs generated with metadata contain valid XMP metadata readable by standard tools
- [ ] `dc:subject` contains tags from the merged data (YAML/TOML/CLI)
- [ ] `xmpMM:DocumentID` is consistent across builds with identical inputs
- [ ] `xmpMM:VersionID` contains the data repo git hash when `data_root` is a git repo
- [ ] When `data_root` is not a git repo, a warning is logged and `xmpMM:VersionID` is absent
- [ ] `xmp:CreatorTool` contains PyreMark version and git hash
- [ ] All date fields reflect the generation timestamp
- [ ] No custom XMP namespaces are used
