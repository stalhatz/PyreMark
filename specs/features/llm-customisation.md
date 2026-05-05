---
size: medium
depends-on: pydantic-classes.md, markdown-cv.md
---

# LLM-driven CV / Cover Letter customisation

## Problem

A user applying to multiple jobs needs a CV or cover letter tailored to each listing.
A single-shot LLM prompt with the full CV schema and the job listing is unreliable:
smaller local models struggle with complex multi-section instructions, context windows
are easily exceeded, and a single validation failure invalidates the entire document.

## Constraints

1. Must work with **local LLMs** — no cloud dependency, no API keys.
2. Must work with **smaller models** (7B–13B parameter range) that fit on consumer hardware.
3. **No single-shot generation** of the full document — the task is decomposed into
   per-section subtasks with bounded context.
4. **Pydantic validation** after every subtask — the LLM output is parsed into the
   corresponding Pydantic model immediately.
5. **Retry-on-failure** — if validation fails, the error message is fed back to the
   LLM with the same prompt, requesting a corrected version. Configurable max retries.
6. Must interface with models that support **structured output** — either:
   - native JSON mode / grammar-constrained decoding, or
   - OpenAI-compatible `response_format` parameter (JSON mode), or
   - JSON-instructable models where a JSON Schema is provided in the system prompt
     and the output is parsed and validated.

## Prerequisites

- [**Pydantic classes**](./pydantic-classes.md) — every section of the YAML data must
  have a corresponding Pydantic model. **Every field must carry docstrings** that
  explain its semantics in plain language — these docstrings are fed to the LLM
  as part of the per-section prompt.
- [**Markdown CV**](./markdown-cv.md) — the frontmatter + body structure must be in
  place so the listing text and the data overrides are available to the LLM pipeline.

## Target state

### Interface

```
pyremark --md note.md --llm [--model <path-or-name>] [--llm-retries <N>]
```

- `--llm` flag triggers the LLM customization pipeline.
- `--model` specifies the model to use (default can be set in TOML config).
- `--llm-retries` configures max retries per section (default: 3).
- All other flags (`--lang`, `-o`, etc.) work as usual — they apply **after**
  the LLM generates content, and participate in the override priority chain.

### How the markdown body is used

- **CV**: the body contains the job listing text. No other role.
- **Cover letter**: the body contains the job listing text. Additionally, the
  body may contain structure hints (e.g., bullet points for paragraphs to include),
  though the primary structure comes from prompt templates (see below).

### Prompt templates as first-class files

Just like HTML templates (`.html.j2`) and CSS templates (`.css.j2`) are files
that the user can override, **prompt templates are files** with a `.prompt.j2`
extension. They live alongside templates and are resolved through the same
`ThemeLoader` search paths so users can override them per-config or per-theme.

Convention:
- One prompt file per document section: `cover_letter_intro.prompt.j2`,
  `experience.prompt.j2`, `education.prompt.j2`, etc.
- A root prompt file per document type: `cv.prompt.j2`, `cover_letter.prompt.j2`
  (defines the section ordering and composition).
- Prompt files are Jinja2 templates — they receive `schema`, `original_data`,
  `listing`, `lang`, `company_context` (from web search) and render the
  final prompt string.

This makes prompts transparent and user-overridable, exactly like the existing
template system.

### Web search integration (cover letter introduction)

For cover letters — especially the introductory paragraph — the LLM needs
context about the company beyond what the job listing provides.

A `--search` flag (or `search` key in TOML config) enables an optional web
search step:

```
pyremark --md note.md --llm --search
```

When enabled:
1. Before any per-section generation, a web search is performed using the
   company name (extracted from the listing) to gather recent news, mission
   statements, product info, etc.
2. The search result is condensed into a `company_context` string and injected
   into the relevant prompt templates (primarily the introduction prompt).
3. The search is **optional** — prompts must degrade gracefully when
   `company_context` is empty.

The search backend is abstracted (DuckDuckGo, SearXNG, etc.) and configurable.
The user can also provide company context manually in frontmatter:

```yaml
config:
  company_context: |
    ACME Corp recently launched a data platform initiative...
```

### Per-section output with rationale

For every section the LLM processes, the output includes an **explanatory
field** alongside the structured data:

```python
class LLMSectionOutput(BaseModel):
    rationale: str = Field(
        description="Explain what was changed and why, or why no changes were made."
    )
    data: SectionModel  # the actual section Pydantic model
```

The `rationale` field is rendered into a **change summary** that becomes part
of the build output (logged, optionally embedded as PDF metadata). This gives
the user visibility into what the LLM decided and why.

When validation fails and retries are exhausted (the section reverts to
original data), the rationale contains the last validation error.

### Output & validation flow per section

```
For section S:

  1. Build prompt P(S):
     - load S.prompt.j2
     - render with: schema(S), original_data(S), listing, lang, company_context
  2. Submit P(S) to LLM → raw JSON output
  3. Parse into LLMSectionOutput(S):
     - rationale(str) + data(SectionModel)
  4. If validation passes:
       → replace data[S] with output.data
       → append output.rationale to change log
  5. If validation fails:
       → retry prompt = P(S) + validation_error + raw_output
       → submit again (up to N retries)
  6. If all retries exhausted:
       → log warning, keep original_data[S]
       → rationale = last validation error
```

### Cover letter structure

A cover letter is not a free-form block of paragraphs. It has a structure:

1. **Introduction** — reference to the position, brief hook, company context.
2. **Body** — 1–3 arguments matching the candidate's experience to the listing.
3. **Closing** — call to action, thanks, availability.
4. **Signature block** — sender name, title (structural, not LLM-generated).

Each of these is a separate sub-section with its own prompt template:
- `cover_letter_intro.prompt.j2`
- `cover_letter_body.prompt.j2`
- `cover_letter_closing.prompt.j2`

Each sub-section has its own Pydantic model (defined in the pydantic-classes
spec). The root `cover_letter.prompt.j2` composes them.

The user can override any of these `.prompt.j2` files to customize the
letter structure, just as they would override a `.html.j2` template to
customize visual layout.

### Model backend abstraction

The primary backend target is any **OpenAI-compatible HTTP endpoint** (vLLM,
LocalAI, Ollama, llama.cpp server, or a real OpenAI API). The baseline
interface mirrors the Chat Completions API with `response_format`:

```python
class StructuredGenerator(Protocol):
    def generate(
        self,
        system_prompt: str,
        prompt: str,
        schema: dict,
        model: str,
    ) -> dict:
        """Return structured dict matching schema, or raise."""
```

Secondary backends (same interface, different transport):
- **Ollama** — supports `format: "json"` in the request.
- **llama.cpp** — supports JSON grammar via `--grammar` or the `grammar` field
  in the server API.
- **vLLM** — supports `response_format` (OpenAI-compatible by design).

The backend is selected via:
- CLI flag: `--llm-backend openai|ollama|llamacpp`
- TOML config key: `llm_backend`
- The endpoint URL is configurable: `--llm-endpoint http://localhost:8000/v1`

### Sections that are hard-skipped

These sections are always excluded from LLM processing regardless of user config:

- `qrcode` — auto-generated, listing-independent.
- `styles`, `script` — build infrastructure, not content.
- `details` — personal details (name, address, contact info, photo) — factual,
  never rewritten.

All other sections are candidates. The user can explicitly include/exclude via
frontmatter:

```yaml
config:
  llm_exclude: [publications, patents]
```

### Change summary

After all sections are processed, a change summary is produced:

```
Changes made by LLM (model: xxx, backend: yyy):
- experience: reordered and rewrote 3 entries to emphasise cloud infrastructure experience. (+rationale)
- education: unchanged (listing does not specify educational requirements).
- cover_letter_intro: rewritten to reference ACME's recent data platform launch.
```

This is logged and optionally stored as metadata in the final PDF (see
[xmp-metadata spec](./xmp-metadata.md)).

## Future considerations

### Listing from an external file
The body could reference a file path instead of containing the listing inline:

```yaml
---
config:
  listing_file: /absolute/path/to/listing.txt
---
```

Must be absolute per the path rules in `markdown-cv.md`.

### Multi-pass refinement (per-section chain)
A section could go through multiple passes — e.g., expand → trim to fit page →
tone-check — rather than a single rewrite. Each pass is its own prompt file
(e.g., `experience_expand.prompt.j2`, `experience_trim.prompt.j2`).

### LLM deciding section inclusion / layout
Instead of a fixed `layout.sections`, a preliminary "layout planning" step
could ask the LLM to select and order sections based on the listing. This
would modify `config.layout.sections` before per-section generation.

### Caching
LLM output per section can be cached keyed by a hash of
(model, listing, original_data, section, lang, company_context).
Useful during iteration — disabled by default, enabled via `--llm-cache`.

### Reproducibility metadata
When `--llm` is used, the markdown note's frontmatter could record:
- Model name / hash
- Backend used
- Prompt template hashes
- Per-section retry counts
- Change summary

This enables deterministic reproduction (cf. the reproducibility section in
`markdown-cv.md`).

### Search backend abstraction
First implementation: DuckDuckGo via `duckduckgo_search` or similar.
Future: configurable SearXNG instance, or a `company_context` file path.

## Non-goals (for this version)

- **Training / fine-tuning** — no model training, no LoRA adapters.
- **RAG** — no vector database, no embedding retrieval beyond optional web search.
- **Multi-turn chat** — each section generation is a single exchange; the system
  does not maintain a conversation state.
- **Image generation** — no photo manipulation or logo generation.
- **Grammar-constrained decoding as requirement** — the OpenAI-compatible API
  baseline uses `response_format`, not grammars. Grammar backends (llama.cpp)
  are secondary.
