import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple

import markdown2 as md
import yaml


logger = logging.getLogger(__name__)


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def split_frontmatter_body(text: str) -> Tuple[dict, str]:
    if not text.startswith("---\n"):
        raise ValueError("No YAML frontmatter found: file must start with '---'")

    lines = text.split("\n")
    end_line = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_line = i
            break

    if end_line is None:
        raise ValueError(
            "Malformed YAML frontmatter: no closing '---' delimiter found"
        )

    frontmatter_text = "\n".join(lines[1:end_line])
    body = "\n".join(lines[end_line + 1 :])

    metadata = yaml.safe_load(frontmatter_text) if frontmatter_text.strip() else {}
    if not isinstance(metadata, dict):
        raise ValueError("YAML frontmatter must be a mapping (key-value pairs)")
    return metadata, body


def metadata_to_yaml_lines(metadata: dict) -> List[str]:
    yaml_text = yaml.dump(
        metadata,
        default_flow_style=False,
        explicit_start=False,
        indent=4,
        allow_unicode=True,
        width=float("inf"),
    )
    return yaml_text.split("\n")


def body_to_html_lines(body: str) -> List[str]:
    lines = body.split("\n")
    lines = [line for line in lines if line.strip()]
    html_lines = []
    for line in lines:
        line = line.strip()
        if line:
            output_line = md.markdown(line)
            output_line = output_line.strip().replace("\n", "")
            html_lines.append(output_line)
    return html_lines


def build_text_yaml(html_lines: List[str]) -> List[str]:
    dict_object = {"text": html_lines}
    yaml_text = yaml.dump(
        dict_object,
        default_flow_style=False,
        explicit_start=False,
        indent=4,
        allow_unicode=True,
        width=float("inf"),
    )
    return yaml_text.split("\n")


def write_lines(path: str, lines: List[str]) -> None:
    with open(path, "w") as f:
        f.writelines(line + "\n" for line in lines)


def transform_md_to_yaml(markdown_content: str) -> list[str]:
    """Parse markdown with optional YAML front matter into YAML lines.

    markdown_content: raw markdown string (may start with --- frontmatter).

    Returns: list of YAML lines containing metadata and body text.

    Raises:
        ValueError: if frontmatter is present with no closing delimiter or is not a mapping.
    """
    if markdown_content.startswith("---\n"):
        metadata, body = split_frontmatter_body(markdown_content)
    else:
        metadata, body = {}, markdown_content

    html_lines = body_to_html_lines(body)
    return metadata_to_yaml_lines(metadata) + build_text_yaml(html_lines)


def parse_markdown_config(md_path: str) -> dict:
    """Parse a markdown file with PyreMark-namespaced frontmatter.

    The frontmatter must contain a ``pyremark`` key whose value is a dict with
    the build instructions.  All other top-level keys are free-form metadata
    and are silently ignored.

    md_path: absolute or relative path to a .md file.

    Returns: {"extends": str, "config": dict|None, "data": dict|None, "body": str}

    Raises:
        ValueError: if pyremark is missing or not a dict, if extends is
        missing inside pyremark, if extends is not an absolute path, or if
        unknown keys appear inside pyremark.
        FileNotFoundError: if the file does not exist.
    """
    PYREMARK_VALID_KEYS = {"extends", "config", "data"}
    text = read_file(md_path)
    metadata, body = split_frontmatter_body(text)

    pyremark = metadata.get("pyremark")
    if pyremark is None:
        raise ValueError(
            "Markdown frontmatter must include a 'pyremark' key containing "
            "the build configuration (extends, config, data)."
        )
    if not isinstance(pyremark, dict):
        raise ValueError(
            "'pyremark' must be a mapping (dict) containing the build configuration."
        )

    if "extends" not in pyremark:
        raise ValueError(
            "'pyremark' must include an 'extends' key with an absolute path "
            "to a TOML build configuration."
        )

    extends_path = pyremark.get("extends")
    if not os.path.isabs(extends_path):
        raise ValueError(
            f"extends path must be absolute, got relative path: '{extends_path}'"
        )

    config_block = pyremark.get("config")
    if config_block is not None and not isinstance(config_block, dict):
        raise ValueError(
            f"'pyremark.config' must be a mapping (dict), got: {type(config_block).__name__}"
        )

    data_block = pyremark.get("data")
    if data_block is not None and not isinstance(data_block, dict):
        raise ValueError(
            f"'pyremark.data' must be a mapping (dict), got: {type(data_block).__name__}"
        )

    # unknown = set(pyremark.keys()) - PYREMARK_VALID_KEYS
    # if unknown:
    #     raise ValueError(
    #         f"Unknown keys in 'pyremark' frontmatter: {sorted(unknown)}. "
    #         f"Allowed keys are: {sorted(PYREMARK_VALID_KEYS)}."
    #     )

    return {
        "extends": extends_path,
        "config": config_block,
        "data": data_block,
        "body": body,
    }


def body_to_data_dict(body: str) -> dict | None:
    """Convert markdown body text to a cover-letter data dict.

    body: raw markdown body text (paragraphs separated by blank lines).

    Returns: {"text": [html_paragraphs]} or None if body is empty/whitespace-only.
    """
    html_lines = body_to_html_lines(body)
    if not html_lines:
        return None
    return {"text": html_lines}


def transform_md_to_yaml_html(input_path: str, output_path: str) -> None:
    text = read_file(input_path)
    lines = transform_md_to_yaml(text)
    write_lines(output_path, lines)

def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.md> <output.yaml>")
        sys.exit(1)
    try:
        transform_md_to_yaml_html(sys.argv[1], sys.argv[2])
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
