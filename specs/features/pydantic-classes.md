---
size: medium
---
# Add Pydantic classes for yaml data

Create pydantic data classes that will be used to instantiate and thus auto-validate a single object corresponding to a full cv (and/or cover letter)

## Concerns
- How do we translate the existing i18n mechanism to a class that represents any possible value string?
    - str -> not translatable
    - dictionary -> translatable
        - "def" field used for every language that doesn't have an explicit translation
        - ISO-639-1 language code to define a language specific translation
        - If no "def" field and no language field -> invalid
- How can we bring our existing (implicit) schema closer to [JSON Resume](https://jsonresume.org) without losing any part of our expressivity
    - We must investigate multiple scenarios
    - We must convert existing data to the new version of the format

# Non-functional constraints
- Good semantic documentation of every field (given that value validity is taken care of by pydantic)
    - LLMs need to be able to understand what each value corresponds to
- Introduce text limit hints. This will help LLMs (and manual users) better create their CVs. For example:
    - A title shouldn't be more than 10 words or 50 character
    - The text of the pitch shouldn't be above 300 characters
    - The number of items per line in knowledge shouldn't exceed 5
        - Otherwise more categories should be created
    - Can pydantic show warnings when such limits are being reached
    

## Goal:
- Integration with LLMs
- Automatic data validation
- Automatic JSON Schema creation

---

## Decisions *(2026-05-06)*

See [decisions.md](../decisions.md) for full rationale on each.

| # | Decision |
|---|----------|
| 1 | **TranslatableStr** — `str \| dict[str, str]`, validates ISO-639-1 / `"def"` keys, no language constraints |
| 2 | **CVDate** — `{year, month?}`, no day precision. `DateField = CVDate \| DateRange`. No bare strings survive validation |
| 3 | **Rendering metadata** — `template`, `id`, `classes` extracted to separate `layout.yaml` |
| 4 | **Lines as dicts** — retained as `dict[str, LineItem]` for named-key override support |
| 5 | **JSON Resume** — converter tool, no section rename |
| 6 | **Text limits** — `x_limit_hint` in `Field(json_schema_extra=...)`, consumed by both JSON Schema and runtime warnings |
| 7 | **Separate document models** — `CVDocument` and `CoverLetterDocument` as distinct root types |


