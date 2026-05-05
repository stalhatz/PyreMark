---
status: draft
area: testing
---

# Enhance unit-test coverage for python source code

## Goal

Bring the two Python modules under systematic unit-test coverage by:

1. Writing tests for every callable that lacks them.
2. ~~Adding type hints and docstrings~~ *(completed — every function signature in both modules is now annotated; docstrings added to all 29 functions)*
3. ~~Cleaning up test infrastructure~~ *(completed — all file-writing tests use `tmp_path` via `--intermediate-dir`, no more hardcoded `css/styles.css` or `html/tmp.html`)*

---

## Methodology for finding test cases

For each function, the agent **must** apply the following 4-step process and **record the analysis as a top-of-file or top-of-class comment** in the relevant test file:

```python
# Branch analysis for <function_name>:
# 1. Branch tree:   (every if/elif/else/for/try/return)
# 2. Input domain:  (nulls, empties, singletons, nesting, type boundaries)
# 3. Call sites:    (what the rest of the codebase actually passes)
# 4. Contract:      (what the name/docstring promises)
```

1. **Trace the branch tree** — every `if`, `elif`, `else`, `for`, `try/except`, `return`.
2. **Identify interesting input values** — null, empty, single-element, multi-element, nested, type boundaries.
3. **Check the call sites** — what shapes does the rest of the codebase actually pass? (This anchors tests in reality and prevents over-testing unreachable paths.)
4. **Identify the contract** — what does the function's name, comment, or (new) docstring promise?

The Cartesian product of (2) across parameters, reduced by equivalence, is the test matrix.

---


## Test cases

### Naming convention

Use descriptive names. Prefer parametrized tests (`@pytest.mark.parametrize`) over copy-paste test functions.  
Group tests for a function under a test class when there are many cases.

### Fixtures

Create a `conftest.py` in `tests/` with:

- `tmp_yaml_file` — writes a dict to a `tmp_path` yaml file, returns the path.
- `tmp_jinja2_template` — writes a simple jinja2 template string to a `tmp_path` file.
- `sample_data_dict` — a small realistic dict shaped like real CV data.

Do **not** write a fixture that replicates the full `themes/` directory — use the existing `testdata/` for that.

---

### `deep_merge(d1: Any, d2: Any, replace: bool = False) -> Any`

Branch tree:
```
if both d1 and d2 are dicts
  → return {**d1, **d2, shared keys merged recursively}
elif not replace
  → return [*flatten(d1), *flatten(d2)]
else
  → return d2
```

Test matrix:

| d1 | d2 | replace | Expected behaviour |
|---|---|---|---|
| `{"a":1}` | `{"b":2}` | `False` | `{"a":1, "b":2}` — disjoint keys |
| `{"a":1}` | `{"a":1}` | `False` | `{"a":1}` — identical values kept |
| `{"a":{"x":1}}` | `{"a":{"y":2}}` | `False` | `{"a":{"x":1,"y":2}}` — nested merge |
| `{"a":1}` | `{"a":2}` | `False` | `{"a":[1,2]}` — conflict → bundled list |
| `{"a":1}` | `{"a":2}` | `True` | `{"a":2}` — conflict → d2 wins |
| `{"a":[1]}` | `{"a":2}` | `False` | `{"a":[1,2]}` — flatten existing list |
| `1` | `2` | `False` | `[1, 2]` — non-dict bundling |
| `1` | `2` | `True` | `2` — non-dict, replace wins |
| `1` | `[2]` | `False` | `[1, 2]` — flatten d2 list |
| `{}` | `{}` | `False` | `{}` |
| `{"a":{"b":{"c":1}}}` | `{"a":{"b":{"d":2}}}` | `False` | 3-level nested merge |
| Complex | Complex | `True` | d2 completely replaces conflicting leaves |

---

### `tr(prop, lang=None, default=None)`

Branch tree:
```
if isinstance(prop, dict):
  if lang is not None and lang in prop  → return prop[lang]
  elif "def" in prop                    → return prop["def"]
  else                                  → return default
else:
  if prop is not None  → return prop
  else                 → return default
```

Test matrix:

| prop | lang | default | Expected |
|---|---|---|---|
| `{"en":"hello","fr":"bonjour"}` | `"en"` | `None` | `"hello"` |
| `{"en":"hello","def":"bonjour"}` | `"fr"` | `None` | `"bonjour"` → falls back to "def" |
| `{"en":"hello"}` | `None` | `None` | `None` → no "def", no lang → default |
| `{"en":"hello"}` | `None` | `"n/a"` | `"n/a"` |
| `"hello"` | `"en"` | `None` | `"hello"` → string passthrough |
| `None` | `"en"` | `"fallback"` | `"fallback"` |
| `None` | `"en"` | `None` | `None` |
| `{"def":"default_val"}` | `None` | `None` | `"default_val"` |
| `{"def":"default_val"}` | `"en"` | `None` | `"default_val"` → lang not in prop, falls to "def" |

---

### `overlay(base: dict, top: dict) -> dict`

Contract: already returns a **new** dict. `top` takes precedence. `None` in `top` does not overwrite an existing `base` key, but sets `None` for keys missing in `base`.

Test matrix:

| base | top | Expected | Notes |
|---|---|---|---|
| `{"a":1}` | `{"b":2}` | `{"a":1,"b":2}` | New keys from top |
| `{"a":1}` | `{"a":2}` | `{"a":2}` | top overwrites |
| `{"a":1}` | `{"a":None}` | `{"a":1}` | None does not overwrite |
| `{}` | `{"a":None}` | `{"a":None}` | None propagated for missing key |
| `{"a":1,"b":2}` | `{"b":None,"c":3}` | `{"a":1,"b":2,"c":3}` | Mixed: overwrite, preserve, new |
| `{}` | `{}` | `{}` | Empty |
| `{"a":1}` | `{}` | `{"a":1}` | No top keys |
| Ensure base unmodified | — | — | Assert `base` is same dict after call |

---

### `readYamlData(yamlFiles: list[str]) -> dict`

Contract: reads one or more yaml files, merges them left-to-right via `deep_merge` (replace=False).

*Pending refactoring:* adding an optional `layout` parameter is still planned (see execution order).

Test matrix:

| yamlFiles | Behaviour |
|---|---|
| `[file1]` (valid yaml) | Returns parsed dict |
| `[file1, file2]` (disjoint) | Merged union |
| `[file1, file2]` (overlapping) | `deep_merge` behaviour |
| `[file1]` with `.txt` extension | `Raises ValueError` |
| Empty yaml file | Returns `{}` |
| Invalid yaml content | `Raises yaml.YAMLError` |

Use `tmp_yaml_file` fixture from conftest.

---

### `renderTemplateAndWriteToFile(template_filename: str | None, data: dict, output_filename: str, search_paths: list[str] | None = None) -> None`

Contract: Loads jinja2 template from `search_paths`, renders with `data`, writes to `output_filename`. Raises `ValueError` if `template_filename` is `None`.

Test matrix:

| search_paths | template_filename | data | Behaviour |
|---|---|---|---|
| `[tmp_dir]` | existing template | `{"name":"world"}` | `Hello world` written to `output_filename` |
| `[tmp_dir]` | non-existent template | any | `Raises TemplateNotFound` |
| `None` | — | — | Defaults to `["."]` |
| Multiple paths with same template name | — | — | First path wins |
| any | `None` | any | `Raises ValueError` |
| any | `""` | any | `Raises TemplateNotFound` |

Use `tmp_jinja2_template` fixture.

---

### `generate_qr_code(url: str, output_path: str) -> None`

Contract: generates a QR code PNG for `url` and saves to `output_path`.

| url | output_path | Behaviour |
|---|---|---|
| `"https://example.com"` | `tmp_path / "qr.png"` | File exists, size > 100 bytes |
| `""` | `tmp_path / "qr.png"` | Valid QR for empty string (still generates) |
| `None` | — | `AttributeError` (from `hashlib`) — this is current behaviour, document in test |

Note: Two `# pyright: ignore` comments are present on `qrcode.constants` (reportAttributeAccessIssue) and `img.save()` (reportArgumentType) due to incomplete third-party stubs.

---

### `createQRCode(data: dict, lang: str, path: str) -> None`

Contract (after refactoring): iterates sections in `data`, for each section with `template == "qr-code.html.j2"`, resolves its `link` via `tr(linkSection, lang)`, generates QR image in `path`, and sets `section["qr_image"]`.

*Pending refactoring:* rename `path` to `img_dir` (see refactoring task 2 in execution order).

Test matrix:

| data | lang | img_dir | Behaviour |
|---|---|---|---|
| One qr-code section with `link={"en":"https://..."}` | `"en"` | `tmp_path` | QR file created at `tmp_path / "qr_<hash>.png"`, `section["qr_image"]` set |
| One qr-code section with link as plain string | `"en"` | `tmp_path` | Same, works without `tr` |
| One qr-code section with `link={"en": "..."}`, lang=`"fr"` | `"fr"` | `tmp_path` | Uses `tr` fallback ("def" or None → skipped) |
| No qr-code sections | `"en"` | `tmp_path` | Nothing happens |
| Section with `template="qr-code.html.j2"` but no `link` key | `"en"` | `tmp_path` | Skipped, warning logged |
| Section with `link=None` | `"en"` | `tmp_path` | Skipped |
| Multiple qr-code sections | `"en"` | `tmp_path` | Multiple images created |
| Verify `section["qr_image"]` format | `"en"` | `tmp_path` | `section["qr_image"]` starts with `"../img/"` |

---

### `transform_md_to_yaml(markdown_content)` (planned new function in `transform_md_to_yaml_html.py`)

*Not yet extracted.* Contract: Parses markdown with optional YAML front matter (between `---` markers). Returns a YAML string containing both metadata and body text.

This would be the extracted core of `tranformMD` — see refactoring task 3 in execution order.

| markdown_content | Behaviour |
|---|---|
| `---\ntitle: Hello\n---\n\nBody text` | YAML with metadata + body |
| `No front matter, just body` | YAML with empty metadata + body |
| `---\na: 1\n---\n\nLine 1\nLine 2` | Multiline body |
| `---\n---\n\nBody` | Empty metadata |
| `` (empty string) | Edge case — document current behaviour |
| Metadata with `---` in body content | The `---` split logic may misbehave — document in test |

---

### Agent work rules for test failures

When the agent writes a test and it fails:

1. **Inspect the failure.** Is the function's behaviour clearly wrong (wrong type, crashes on obvious input, violates its own contract)?

2. **If clearly wrong:** Fix the implementation. Add a comment explaining the fix. The test represents the correct contract.

3. **If ambiguous:** The spec, name, and comments don't disambiguate. In that case:
   - Adjust the test to match the actual behaviour (not the other way around).
   - Leave a `# TODO: clarify intended behaviour` comment on the function.
   - **Report the ambiguity to the user directly** (via the chat/conversation) so it can be resolved before the commit. Do not commit unresolved ambiguity.

4. **If the test itself is wrong** (bad fixture, wrong expected value): Fix the test.

---

## Infrastructure tasks

### 1. `conftest.py`

Create `tests/conftest.py` with:

```python
import pytest
from pathlib import Path

@pytest.fixture
def tmp_yaml_file(tmp_path):
    """Write a dict to a yaml file in tmp_path, return the path."""
    import yaml
    def _write(data: dict, name: str = "data.yaml") -> Path:
        path = tmp_path / name
        with open(path, "w") as f:
            yaml.dump(data, f)
        return path
    return _write

@pytest.fixture
def tmp_jinja2_template(tmp_path):
    """Write a jinja2 template to tmp_path, return the path."""
    def _write(content: str, name: str = "template.j2") -> Path:
        path = tmp_path / name
        with open(path, "w") as f:
            f.write(content)
        return path
    return _write

@pytest.fixture
def sample_data_dict():
    """A small realistic data dict shaped like CV data."""
    return {
        "data": {
            "details": {"name": "Test", "template": "preambule.html.j2"},
            "experience": {
                "title": "Work",
                "template": "general_parser.html.j2",
                "lines": {
                    "job1": {"date": "2020", "title": "Engineer"},
                },
            },
        },
        "sections": ["details", "experience"],
        "lang": "en",
    }
```

### 2. `tmp_path` hygiene

- Every test that writes files **must** use `tmp_path`.
- ~~Remove the existing tests that read from production paths~~ *(completed — 6 integration tests now pass `--intermediate-dir` pointing to `tmp_path` and read from it)*
- ~~Convert them to use `--output` pointing into `tmp_path`~~ *(completed)*
- Delete `test.html` from the project root if it was a leftover artefact.

### 3. `--intermediate-dir` CLI flag (completed)

Added a `--intermediate-dir` CLI argument (default `"."`) that controls where intermediate build
artifacts (`html/tmp.html`, `css/styles.css`, `js/tmp.js`, `img/`) are written. `BuildConfig.intermediate_dir`
stores the value; `resolve_build_config` omits the field when `None`, letting the `BuildConfig` dataclass
default (`"."`) apply. The `__main__` block derives all four artifact paths from `config.intermediate_dir`
and ensures the subdirectories exist via `os.makedirs`.

---

## Execution order

1. `conftest.py` (so other tests can use fixtures)
2. ~~Type hints + docstrings~~ *(completed)*
3. ~~`--intermediate-dir` CLI flag + `BuildConfig.intermediate_dir`~~ *(completed)*
4. ~~Fix existing integration tests that use hardcoded paths → `tmp_path`~~ *(completed)*
5. Refactoring tasks: `createQRCode` (add `img_dir` parameter), `transform_md_to_yaml` (extract from `transform_md_to_yaml_html`)
6. Pure+untested functions: `deep_merge`, `tr`, `overlay`, `readYamlData`, `renderTemplateAndWriteToFile`, `generate_qr_code`
7. `createQRCode` (after the parameter injection)
8. `transform_md_to_yaml` (after the extraction)
9. Delete `test.html` if present

---

## What success looks like

- Every function in source files has at least one test case.
- ✅ All file-writing tests use `tmp_path` — no hardcoded `css/styles.css` or `html/tmp.html`.
- `deep_merge`, `tr`, `overlay`, `readYamlData`, `generate_qr_code`, `createQRCode`, `renderTemplateAndWriteToFile`, `transform_md_to_yaml` have full branch coverage.
- `createQRCode` accepts an optional `img_dir` parameter.
- ✅ Type hints — completed on every function signature in both modules.
- ✅ Docstrings — completed on all 29 functions in source (compact format: params, Returns, Raises, Side-effects).
- ✅ `overlay` (`mergeDicts`) — already returns a new dict, no mutation occurs.
- ✅ `--intermediate-dir` CLI flag — controls build artifact paths, tests use it via `tmp_path`.
- `conftest.py` exists with reusable fixtures.
