import pytest
import sys
import tempfile
from pathlib import Path

test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir.parent / "src"))

from transform_md_to_yaml_html import (
    read_file,
    split_frontmatter_body,
    metadata_to_yaml_lines,
    body_to_html_lines,
    build_text_yaml,
    write_lines,
    transform_md_to_yaml_html,
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
