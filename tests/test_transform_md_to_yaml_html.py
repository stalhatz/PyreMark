import pytest
import sys
import tempfile
from pathlib import Path

test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir.parent))

from src.transform_md_to_yaml_html import (
    read_file,
    split_frontmatter_body,
    metadata_to_yaml_lines,
    body_to_html_lines,
    build_text_yaml,
    write_lines,
    transform_md_to_yaml,
    transform_md_to_yaml_html,
    parse_markdown_config,
    body_to_data_dict,
)


# --- read_file ---

def test_read_file(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello")
    assert read_file(str(f)) == "hello"


def test_read_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_file("/nonexistent/path.md")


# --- split_frontmatter_body ---

SAMPLE_MD = """\
---
key1: value1
key2:
  sub: nested
---

This is the body.

Second paragraph.
"""


def test_split_frontmatter_body_valid():
    metadata, body = split_frontmatter_body(SAMPLE_MD)
    assert metadata == {"key1": "value1", "key2": {"sub": "nested"}}
    assert body == "\nThis is the body.\n\nSecond paragraph.\n"


def test_split_frontmatter_body_no_delimiter():
    with pytest.raises(ValueError, match="must start with '---'"):
        split_frontmatter_body("plain text without frontmatter")


def test_split_frontmatter_body_no_closing():
    with pytest.raises(ValueError, match="no closing"):
        split_frontmatter_body("---\nkey: value\n")


def test_split_frontmatter_body_empty():
    metadata, body = split_frontmatter_body("---\n---\nbody text")
    assert metadata == {}
    assert body == "body text"


def test_split_frontmatter_body_not_mapping():
    with pytest.raises(ValueError, match="must be a mapping"):
        split_frontmatter_body("---\n[1, 2, 3]\n---\nbody")


# --- metadata_to_yaml_lines ---

def test_metadata_to_yaml_lines():
    metadata = {"name": "Alex", "age": 30}
    lines = metadata_to_yaml_lines(metadata)
    assert "name: Alex" in lines
    assert "age: 30" in lines


def test_metadata_to_yaml_lines_empty():
    assert metadata_to_yaml_lines({}) == ['{}', '']


# --- body_to_html_lines ---

def test_body_to_html_lines():
    body = "First line\n\nSecond line\n\nThird line"
    html = body_to_html_lines(body)
    assert len(html) == 3
    assert html[0] == "<p>First line</p>"
    assert html[1] == "<p>Second line</p>"
    assert html[2] == "<p>Third line</p>"


def test_body_to_html_lines_blank_lines_filtered():
    body = "Line one\n\n\n\nLine two"
    html = body_to_html_lines(body)
    assert len(html) == 2


def test_body_to_html_lines_empty():
    assert body_to_html_lines("") == []


def test_body_to_html_lines_whitespace_only():
    assert body_to_html_lines("   \n  \n  ") == []


# --- build_text_yaml ---

def test_build_text_yaml():
    html_lines = ["<p>First</p>", "<p>Second</p>"]
    lines = build_text_yaml(html_lines)
    assert "text:" in lines
    assert "<p>First</p>" in "".join(lines)
    assert "<p>Second</p>" in "".join(lines)


def test_build_text_yaml_empty():
    lines = build_text_yaml([])
    assert any("text:" in line for line in lines)
    assert any("[]" in line for line in lines)


# --- write_lines ---

def test_write_lines(tmp_path):
    f = tmp_path / "out.yaml"
    write_lines(str(f), ["line one", "line two"])
    content = f.read_text()
    assert content == "line one\nline two\n"


def test_write_lines_empty(tmp_path):
    f = tmp_path / "out.yaml"
    write_lines(str(f), [])
    content = f.read_text()
    assert content == ""


# --- integration: transform_md_to_yaml_html ---

def test_transform_md_to_yaml_html_end_to_end(tmp_path):
    md_file = tmp_path / "input.md"
    yaml_file = tmp_path / "output.yaml"

    md_file.write_text("""\
---
title: Cover Letter
author: Alex
---

First paragraph.

Second paragraph here.
""")

    transform_md_to_yaml_html(str(md_file), str(yaml_file))
    result = yaml_file.read_text()

    assert "title: Cover Letter" in result
    assert "author: Alex" in result
    assert "<p>First paragraph.</p>" in result
    assert "<p>Second paragraph here.</p>" in result


def test_transform_md_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        transform_md_to_yaml_html("/no/such/file.md", str(tmp_path / "out.yaml"))


# --- test with real fixture file ---

def test_with_fixture_file(tmp_path):
    fixture = test_dir.parent / "testdata" / "md" / "cover_letter.md"
    yaml_file = tmp_path / "out.yaml"

    transform_md_to_yaml_html(str(fixture), str(yaml_file))
    result = yaml_file.read_text()

    assert "Alex Demo" in result
    assert "Hiring Manager" in result
    assert "April 25, 2026" in result
    assert "<p>I am writing to express my interest.</p>" in result
    assert "<p>Throughout my career, I have led teams.</p>" in result
    assert "<p>I look forward to hearing from you.</p>" in result


# Branch analysis for transform_md_to_yaml:
# 1. Branch tree:
#    if markdown_content.startswith("---\n") → split_frontmatter_body
#    else → metadata={}, body=markdown_content
#    return metadata_to_yaml_lines(metadata) + build_text_yaml(body_to_html_lines(body))
# 2. Input domain: str with frontmatter, str without, empty str, str with --- in body
# 3. Call sites: transform_md_to_yaml_html — pass raw markdown text
# 4. Contract: Parse markdown with optional YAML front matter (between --- markers).
#    Returns list of YAML lines containing both metadata and body text.

def test_transform_md_to_yaml_with_frontmatter():
    content = "---\ntitle: Hello\n---\n\nBody text"
    result = transform_md_to_yaml(content)
    result_str = "\n".join(result)
    assert "title: Hello" in result_str
    assert "<p>Body text</p>" in result_str

def test_transform_md_to_yaml_no_frontmatter():
    content = "Just body text"
    result = transform_md_to_yaml(content)
    result_str = "\n".join(result)
    assert "<p>Just body text</p>" in result_str

def test_transform_md_to_yaml_multiline_body():
    content = "---\na: 1\n---\n\nLine 1\nLine 2"
    result = transform_md_to_yaml(content)
    result_str = "\n".join(result)
    assert "a: 1" in result_str
    assert "<p>Line 1</p>" in result_str
    assert "<p>Line 2</p>" in result_str

def test_transform_md_to_yaml_empty_metadata():
    content = "---\n---\n\nBody"
    result = transform_md_to_yaml(content)
    result_str = "\n".join(result)
    assert "<p>Body</p>" in result_str

def test_transform_md_to_yaml_empty_string():
    """Empty string: body_to_html_lines returns [], build_text_yaml produces {'text': []}."""
    result = transform_md_to_yaml("")
    result_str = "\n".join(result)
    assert "text:" in result_str

def test_transform_md_to_yaml_dash_in_body():
    """--- embedded in body text line (not on its own line) is handled correctly."""
    content = "---\ntitle: Test\n---\n\nBody with --- inline."
    result = transform_md_to_yaml(content)
    result_str = "\n".join(result)
    assert "title: Test" in result_str
    assert "Body with --- inline" in result_str

def test_transform_md_to_yaml_dash_line_in_body():
    """--- on its own line in body is treated as body content (markdown horizontal rule).
    This is a known limitation: split_frontmatter_body finds the first --- as closing."""
    content = "---\ntitle: Test\n---\n\nParagraph 1\n\n---\n\nParagraph 2"
    result = transform_md_to_yaml(content)
    result_str = "\n".join(result)
    assert "title: Test" in result_str
    assert "Paragraph 1" in result_str
    # --- in body is converted to <hr /> by markdown2
    assert "<hr />" in result_str
    assert "Paragraph 2" in result_str


# --- parse_markdown_config ---

def test_parse_md_config_valid(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("""\
---
pyremark:
  extends: /absolute/path/to/config.toml
  config:
    lang: fr
  data:
    sender:
      name: Alex
---

Body text here.
""")
    result = parse_markdown_config(str(md_file))
    assert result["extends"] == "/absolute/path/to/config.toml"
    assert result["config"] == {"lang": "fr"}
    assert result["data"] == {"sender": {"name": "Alex"}}
    assert result["body"] == "\nBody text here.\n"


def test_parse_md_config_missing_pyremark(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("---\ntitle: My Note\n---\n\nBody")
    with pytest.raises(ValueError, match="must include a 'pyremark' key"):
        parse_markdown_config(str(md_file))


def test_parse_md_config_pyremark_not_dict(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("---\npyremark: not_a_dict\n---\n\nBody")
    with pytest.raises(ValueError, match="must be a mapping"):
        parse_markdown_config(str(md_file))


def test_parse_md_config_missing_extends(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("---\npyremark:\n  config:\n    lang: fr\n---\n\nBody")
    with pytest.raises(ValueError, match="must include an 'extends' key"):
        parse_markdown_config(str(md_file))


def test_parse_md_config_relative_extends(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("---\npyremark:\n  extends: relative/path/config.toml\n---\n\nBody")
    with pytest.raises(ValueError, match="must be absolute"):
        parse_markdown_config(str(md_file))


def test_parse_md_config_unknown_key_inside_pyremark(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("""\
---
pyremark:
  extends: /absolute/config.toml
  unknown_key: value
---
Body
""")
    with pytest.raises(ValueError, match="Unknown keys in 'pyremark'"):
        parse_markdown_config(str(md_file))


def test_parse_md_config_non_pyremark_keys_ignored(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("""\
---
title: My Application
author: Alex
pyremark:
  extends: /absolute/config.toml
  config:
    lang: fr
---
Body text.
""")
    result = parse_markdown_config(str(md_file))
    assert result["extends"] == "/absolute/config.toml"
    assert result["config"] == {"lang": "fr"}
    assert result["data"] is None
    assert result["body"] == "Body text.\n"


def test_parse_md_config_body_preserved(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("---\npyremark:\n  extends: /absolute/config.toml\n---\n\nLine one.\n\nLine two.\n")
    result = parse_markdown_config(str(md_file))
    assert result["config"] is None
    assert result["data"] is None
    assert result["body"] == "\nLine one.\n\nLine two.\n"


def test_parse_md_config_no_frontmatter(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("Just body, no frontmatter")
    with pytest.raises(ValueError, match="must start with '---'"):
        parse_markdown_config(str(md_file))


# --- body_to_data_dict ---

def test_body_to_data_dict_normal():
    body = "First paragraph.\n\nSecond paragraph."
    result = body_to_data_dict(body)
    assert result is not None
    assert "text" in result
    assert len(result["text"]) == 2
    assert "<p>First paragraph.</p>" in result["text"]
    assert "<p>Second paragraph.</p>" in result["text"]


def test_body_to_data_dict_empty():
    assert body_to_data_dict("") is None


def test_body_to_data_dict_whitespace_only():
    assert body_to_data_dict("  \n  \n  ") is None
