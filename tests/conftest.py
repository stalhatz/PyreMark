import pytest
from pathlib import Path
import subprocess


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


@pytest.fixture
def tmp_git_repo(tmp_path):
    """Create a temporary git repository with an initial commit."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, capture_output=True)
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True)
    return tmp_path
