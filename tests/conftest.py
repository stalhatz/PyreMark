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
