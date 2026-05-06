# Architecture Decisions

## Decision 1: TranslatableStr type

**Date**: 2026-05-06

**Context**: The existing i18n mechanism represents text fields as either a plain `str` (non-translatable) or a `dict[str, str]` (translatable) where keys are either `"def"` (default/fallback) or 2-letter ISO-639-1 language codes.

**Decision**: Create a custom Pydantic type `TranslatableStr` that:
- Accepts `str` — stores as-is
- Accepts `dict[str, str]` — validates that at least one key is `"def"` or matches `^[a-z]{2}$`
- Rejects empty dicts or dicts with no valid keys
- No per-field or global language constraints (no whitelist, no completeness requirement across fields)

**Rationale**: Clean validation of the existing YAML format without migration cost. The resolver function `tr()` remains a separate runtime concern operating on raw dicts.

**See also**: [specs/features/pydantic-classes.md](./specs/features/pydantic-classes.md)

## Decision 2: CVDate type

**Date**: 2026-05-06

**Context**: Dates in the existing YAML data are free-form strings (`"2019 - 2022"`, `"2022 - Present"`, `"2020"`). Validation benefits from structured date representations. Day-level precision has no use case in a CV context.

**Decision**:
- `CVDate(BaseModel)` with `year: int`, `month: int | None = None`. No day field.
- `DateRange(BaseModel)` with `start: CVDate`, `end: CVDate | None = None` (None = ongoing / Present).
- `DateField = CVDate | DateRange` — no unvalidated strings survive Pydantic parsing.
- Free-form legacy strings handled by a `BeforeValidator` on `DateField` that converts `"2019 - 2022"` → `DateRange`, `"2020"` → `CVDate`, etc.

**Rationale**: Structured dates enable the `findDateField` / `sortData` functions to operate on typed attributes instead of regex, and provide better structured output for LLM integration.

**See also**: [specs/features/pydantic-classes.md](./specs/features/pydantic-classes.md)

## Decision 3: Rendering metadata separation

**Date**: 2026-05-06

**Context**: YAML data files currently contain rendering metadata (`template`, `id`, `classes`) intermixed with document content. This merging of concerns complicates validation and pollutes the data schema that LLMs interact with.

**Decision**:
- Extract `template`, `id`, `classes` from YAML data files into a separate `layout.yaml` file at the data root level.
- The build pipeline merges the validated document dict with layout metadata before rendering.
- `layout.yaml` default path: `{config.data_root}/layout.yaml`, overridable via TOML/CLI.

**Rationale**: Content data and rendering directives are unrelated concerns. Separation gives LLMs a clean view of the data schema (no rendering noise) while retaining the ability to customize which template renders which section.

**See also**: [specs/features/pydantic-classes.md](./specs/features/pydantic-classes.md)

## Decision 4: Lines as dicts

**Date**: 2026-05-06

**Context**: Sections like `experience` and `education` store entries as dicts keyed by arbitrary string IDs (e.g., `senior_engineer`, `fullstack_dev`). JSON Resume uses arrays.

**Decision**: Keep `lines` as `dict[str, LineItem]`.

**Rationale**: Named keys enable the deep-merge override story — users (and future LLM pipelines) can modify specific entries by name rather than by array position. This is a core part of PyreMark's configurability philosophy.

**See also**: [specs/features/pydantic-classes.md](./specs/features/pydantic-classes.md)

## Decision 5: JSON Resume alignment

**Date**: 2026-05-06

**Context**: The spec asks to bring the schema closer to JSON Resume. JSON Resume's taxonomy is another ad-hoc classification, not aligned with established occupational taxonomies (SOC, ISCO, ESCO, O*NET, ROME).

**Decision**: Do not rename sections to JSON Resume names. Provide a standalone converter tool (`pyremark convert`) as a separate feature spec.

**Rationale**: Swapping one ad-hoc taxonomy for another adds no value. A converter enables interoperability without sacrificing PyreMark's own ontology.

**See also**: [specs/features/pydantic-classes.md](./specs/features/pydantic-classes.md)

## Decision 6: Text limit hints

**Date**: 2026-05-06

**Context**: The spec requests limit hints (e.g., title ≤ 50 chars, pitch ≤ 300 chars, knowledge items ≤ 5 per line) that serve both LLM prompts and user-facing warnings.

**Decision**:
- Define limits once in `Field(json_schema_extra={"x_limit_hint": {"max_chars": N, "max_words": M, "max_items": K}})`.
- A `ContentModel` base class reads these hints at model validation time and logs warnings when limits are exceeded.
- JSON Schema generation automatically includes the hints for LLM consumption.

**Rationale**: DRY — hints are defined once and consumed by both the JSON Schema (LLM prompts) and the runtime warning hook. Warnings rather than hard rejections keep parse flexibility for human-authored data.

**See also**: [specs/features/pydantic-classes.md](./specs/features/pydantic-classes.md)

## Decision 7: Separate CV and Cover Letter document models

**Date**: 2026-05-06

**Context**: CV and cover letter data have fundamentally different shapes (sections vs sender/receiver/text).

**Decision**: Two separate root models: `CVDocument` and `CoverLetterDocument`.

**Rationale**: A union model would impose unnecessary optionality. Two models reflect the actual data structure and produce cleaner JSON Schemas.

**See also**: [specs/features/pydantic-classes.md](./specs/features/pydantic-classes.md)
