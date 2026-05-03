import pytest
import sys
from pathlib import Path

from copy import deepcopy

test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir.parent / "src"))

from build import yearInDateString

def test_yearInDateString_one_date():
    assert yearInDateString("Hello_World_2030") == "2030"
def test_yearInDateString_two_dates():
    assert yearInDateString("Hello_2033World_2031") == "2033"
def test_yearInDateString_consecutive_numbers():
    assert yearInDateString("Hello_2032031") == "2032"
def test_yearInDateString_no_numbers():
    assert yearInDateString("Hello_World") is None

from build import findDateField
def test_findDateField_single_level():
    inputDate = ("a",{"date":"2023"})
    assert findDateField(inputDate) == 2023
def test_findDateField_double_level():
    inputDate = ("a",{"date": {"fr":"aout 2023","en":"august 2023"}})
    assert findDateField(inputDate) == 2023
def test_findDateField_not_a_tuple():
    inputDate = "hello"
    with pytest.raises(TypeError):
        findDateField(inputDate)

from build import sortDict
def test_sortLines_int():
    inputData = {"a": 1, "v":45 , "c":2}
    # Ascending
    assert sortDict(inputData,True,lambda x:x[1]) == {"a": 1, "c":2 ,"v":45}
    # Descending
    assert sortDict(inputData,False,lambda x:x[1]) == {"v":45, "c":2, "a": 1}


def dict_to_list_of_lists(d):
    if isinstance(d, dict):
        return [[k, dict_to_list_of_lists(v)] for k, v in d.items()]
    elif isinstance(d, (list, tuple)):
        return [dict_to_list_of_lists(item) for item in d]
    else:
        return d

def compareDicts(a,b):

    lla = dict_to_list_of_lists(a)
    llb = dict_to_list_of_lists(b)
    print("\n")
    print(lla)
    print(llb)
    return lla == llb

from build import sortData
def test_sortData():
    d2010 = {"py" : {"date":"2010" , "test":"python"}}
    d2005 = {"by":{"date":"2005" , "best":"bython"}}
    d2007 = {"cy":{"date":"2007" , "cest":"cython"}}


    inputData = {"a": {"b" : {"lines" : d2010 | d2005 | d2007 } } }
    # Ascending
    cloneData = deepcopy(inputData)
    expectedResult = {"a": {"b" : {"lines" : d2010 | d2007 | d2005  } } }
    sortData(cloneData,dsc = True) 
    assert compareDicts(cloneData,expectedResult)
    
    # Descending
    cloneData = deepcopy(inputData)
    expectedResult = {"a": {"b" : {"lines" : d2005 | d2007 | d2010  } } }
    sortData(cloneData,dsc = False) 
    assert compareDicts(cloneData,expectedResult)


# --- Theme system tests ---

from build import ThemeResolver, ThemeLoader

def test_theme_resolver_search_paths():
    resolver = ThemeResolver("default_cv")
    paths = resolver.search_paths()
    assert any("themes/default_cv/j2" in p for p in paths)

def test_theme_resolver_manifest():
    resolver = ThemeResolver("default_cv")
    assert resolver._manifest.get("theme") == "default_cv"
    assert resolver._manifest.get("author") == "PyreMark"

def test_theme_resolver_extends():
    resolver = ThemeResolver("ext_default_cv_example")
    paths = resolver.search_paths()
    # Should contain both child and parent j2 directories
    assert any("ext_default_cv_example" in p for p in paths)
    assert any("/default_cv/" in p for p in paths)
    # Child comes before parent
    child_idx = next(i for i, p in enumerate(paths) if "ext_default_cv_example" in p)
    parent_idx = next(i for i, p in enumerate(paths) if "/default_cv/" in p)
    assert child_idx < parent_idx

def test_theme_loader_resolution():
    resolver = ThemeResolver("default_cv")
    loader = ThemeLoader(resolver.search_paths())
    source, path, _ = loader.get_source(None, "styles.css.j2")
    assert "css/tokens.css.j2" in source
    assert "themes/default_cv" in path

def test_theme_loader_user_override():
    resolver = ThemeResolver("default_cv", user_theme_dir=str(test_dir.parent / "testdata" / "theme"))
    paths = resolver.search_paths()
    loader = ThemeLoader(paths)
    source, path, _ = loader.get_source(None, "preambule.html.j2")
    assert "testdata-override" in source
    assert "testdata/theme" in path

def test_theme_resolver_pre_post_styles():
    resolver = ThemeResolver(
        "default_cv",
        pre_styles=str(test_dir.parent / "testdata" / "pre.css"),
        post_styles=str(test_dir.parent / "testdata" / "post.css"),
    )
    pre = resolver.get_pre_styles()
    post = resolver.get_post_styles()
    assert "pre_styles test" in pre
    assert "post_styles test" in post
    assert "background-color: #ff0000" in pre
    assert "color: #00ff00" in post

def test_theme_resolver_missing_theme():
    with pytest.raises(ValueError, match="Theme 'nonexistent' not found"):
        ThemeResolver("nonexistent")


def test_default_cv_build_output(tmp_path):
    """Theme mode with default_cv should produce valid output files."""
    import subprocess
    css_file = tmp_path / "styles.css"
    html_file = tmp_path / "tmp.html"
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out.pdf").exists()


def test_new_cv_example_renders(tmp_path):
    """new_cv_example should render all data sections without errors."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--theme", "new_cv_example",
            "--intermediate-dir", str(tmp_path),
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out.pdf").exists()
    # CSS should have the new theme's distinct styles
    css = (tmp_path / "css" / "styles.css").read_text()
    assert "'Inter'" in css or "#2563eb" in css or "#eef2ff" in css


def test_ext_default_cv_example_override(tmp_path):
    """ext_default_cv_example should override photo.css with funky frame."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--theme", "ext_default_cv_example",
            "--intermediate-dir", str(tmp_path),
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = (tmp_path / "css" / "styles.css").read_text()
    # Should contain the overridden photo.css
    assert "border: 4px solid #ff6b6b" in css
    assert "saturate(1.5)" in css


def test_pre_styles_inserted_at_beginning(tmp_path):
    """pre_styles should appear at the beginning of compiled CSS."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--theme-pre-styles", "testdata/pre.css",
            "--intermediate-dir", str(tmp_path),
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = (tmp_path / "css" / "styles.css").read_text()
    assert css.startswith("/* pre_styles test")


def test_post_styles_inserted_at_end(tmp_path):
    """post_styles should appear at the end of compiled CSS."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--theme-post-styles", "testdata/post.css",
            "--intermediate-dir", str(tmp_path),
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = (tmp_path / "css" / "styles.css").read_text()
    assert css.strip().endswith("color: #00ff00 !important;\n}")


def test_local_theming_dir_override_priority(tmp_path):
    """User local_theming_dir should take precedence over built-in theme files."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--theme", "default_cv",
            "--local-theming-dir", "testdata/theme",
            "--intermediate-dir", str(tmp_path),
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    html = (tmp_path / "html" / "tmp.html").read_text()
    assert "testdata-override" in html


def test_config_styles_tokens_override(tmp_path):
    """Config [styles] tokens should override CSS variables."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/tokens_tweaked.toml",
            "--intermediate-dir", str(tmp_path),
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = (tmp_path / "css" / "styles.css").read_text()
    assert "--fontSize: 9.5px" in css
    assert "--fontFamily: 'Roboto', 'Helvetica', sans-serif" in css


# --- data_root tests ---

from build import resolve_build_config
from types import SimpleNamespace
import os

def test_data_root_auto_detect_from_toml():
    """Auto-detect data_root as the TOML file's containing directory."""
    toml_path = str(test_dir.parent / "testdata" / "cv" / "single_page.toml")
    args = SimpleNamespace(cv=toml_path, type="cv")
    config = resolve_build_config(args, yaml_files=None, config_file_path=toml_path)
    expected = str((test_dir.parent / "testdata" / "cv").resolve())
    assert config.data_root == expected


def test_data_root_explicit_in_args():
    """--data-root CLI flag should take precedence over auto-detect."""
    toml_path = str(test_dir.parent / "testdata" / "cv" / "single_page.toml")
    custom_root = str(test_dir.parent / "testdata")
    args = SimpleNamespace(cv=toml_path, type="cv", data_root=custom_root)
    config = resolve_build_config(args, yaml_files=None, config_file_path=toml_path)
    assert config.data_root == str((test_dir.parent / "testdata").resolve())


def test_data_root_toml_relative():
    """data_root = '..' in TOML args resolves relative to the TOML file directory."""
    toml_path = str(test_dir.parent / "testdata" / "cv" / "single_page.toml")
    args = SimpleNamespace(cv=toml_path, type="cv", data_root="..")
    config = resolve_build_config(args, yaml_files=None, config_file_path=toml_path)
    expected = str(test_dir.parent / "testdata")
    assert config.data_root == expected


def test_data_root_cli_without_toml_falls_back_to_cwd():
    """CLI-only without a TOML should set data_root to CWD."""
    cwd = str(Path.cwd().resolve())
    args = SimpleNamespace(type="cv")
    config = resolve_build_config(args, yaml_files=None, config_file_path=None)
    assert config.data_root == cwd


def test_yaml_files_resolved_against_data_root():
    """YAML file paths in TOML should be resolved relative to data_root."""
    toml_path = str(test_dir.parent / "testdata" / "cv" / "single_page.toml")
    args = SimpleNamespace(cv=toml_path, type="cv")
    config = resolve_build_config(
        args,
        yaml_files=["../yaml/personal_details.yaml"],
        config_file_path=toml_path,
    )
    expected = str(test_dir.parent / "testdata" / "yaml" / "personal_details.yaml")
    assert config.yaml_files is not None
    assert expected in config.yaml_files


def test_data_root_warning_bad_root(tmp_path):
    """Warning when data_root does not exist."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--data-root", str(tmp_path / "nonexistent"),
            "--type", "CV",
            "--yaml", str(test_dir.parent / "testdata" / "yaml" / "personal_details.yaml"),
            "--output", str(tmp_path / "out.pdf"),
            "--intermediate-dir", str(tmp_path),
        ],
        capture_output=True, text=True
    )
    assert "does not exist" in result.stdout or "does not exist" in result.stderr


def test_data_root_warning_no_yaml_dir(tmp_path):
    """Warning when data_root exists but has no yaml/ subdirectory."""
    import subprocess
    # Create a TOML file in a subdirectory so we can use auto-detect
    toml_dir = tmp_path / "conf"
    toml_dir.mkdir()
    toml_file = toml_dir / "test.toml"
    toml_file.write_text("""type = "cv"\nyaml = []\n""")
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", str(toml_file),
            "--output", str(tmp_path / "out.pdf"),
            "--intermediate-dir", str(tmp_path),
        ],
        capture_output=True, text=True
    )
    assert "no yaml/ directory found" in result.stdout or "no yaml/ directory found" in result.stderr


def test_resolve_user_images_copies_and_rewrites(tmp_path):
    """resolve_user_images should copy image and rewrite path to ../img/<name>."""
    from build import resolve_user_images

    # Setup: create a real image file in data_root
    data_root = str(tmp_path / "data")
    img_src_dir = tmp_path / "data" / "photos"
    img_src_dir.mkdir(parents=True)
    img_file = img_src_dir / "profile.jpg"
    img_file.write_bytes(b"fake image data")

    img_dir = str(tmp_path / "output" / "img")
    os.makedirs(img_dir, exist_ok=True)

    data = {
        "data": {
            "details": {
                "photo": "photos/profile.jpg",
                "firstName": "Test",
            }
        }
    }

    resolve_user_images(data, data_root, img_dir)

    assert data["data"]["details"]["photo"] == "../img/profile.jpg"
    assert data["data"]["details"]["firstName"] == "Test"
    dest = os.path.join(img_dir, "profile.jpg")
    assert os.path.isfile(dest)
    assert open(dest, "rb").read() == b"fake image data"


def test_resolve_user_images_skips_urls_and_abs_paths(tmp_path):
    """URLs and absolute paths should be left untouched."""
    from build import resolve_user_images

    data_root = str(tmp_path)
    img_dir = str(tmp_path / "output" / "img")
    os.makedirs(img_dir, exist_ok=True)

    data = {
        "data": {
            "details": {
                "photo": "https://example.com/photo.jpg",
            }
        },
        "sender": {
            "signaturePhoto": "/absolute/path/sig.png",
        },
    }

    resolve_user_images(data, data_root, img_dir)

    assert data["data"]["details"]["photo"] == "https://example.com/photo.jpg"
    assert data["sender"]["signaturePhoto"] == "/absolute/path/sig.png"


def test_resolve_user_images_keeps_original_on_missing_file(tmp_path):
    """When image file doesn't exist, keep original path and warn."""
    from build import resolve_user_images

    data_root = str(tmp_path)
    img_dir = str(tmp_path / "output" / "img")
    os.makedirs(img_dir, exist_ok=True)

    data = {
        "data": {
            "details": {
                "photo": "img/missing.jpg",
            }
        }
    }

    resolve_user_images(data, data_root, img_dir)

    assert data["data"]["details"]["photo"] == "img/missing.jpg"


def test_data_root_integration(tmp_path):
    """End-to-end: build with a TOML config and verify image is resolved."""
    import subprocess

    data_dir = tmp_path / "data"
    yaml_dir = data_dir / "yaml"
    img_dir = data_dir / "img"
    conf_dir = data_dir / "conf"
    yaml_dir.mkdir(parents=True)
    img_dir.mkdir(parents=True)
    conf_dir.mkdir(parents=True)

    # Create a test image
    test_img = img_dir / "profile.jpg"
    test_img.write_bytes(b"fake image data")

    # Create a minimal YAML with a relative image path
    yaml_file = yaml_dir / "details.yaml"
    yaml_file.write_text("""data:
  details:
    photo: img/profile.jpg
    firstName:
      def: Test
    candidateTitle:
      def: "Test CV"
    template: "preambule.html.j2"
""")

    # Create a TOML config with data_root pointing up from conf/
    toml_file = conf_dir / "test.toml"
    toml_file.write_text("""type = "cv"
data_root = ".."
yaml = ['yaml/details.yaml']

[layout]
sections = ['details']
""")

    out_dir = tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", str(toml_file),
            "--intermediate-dir", str(out_dir),
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr

    copied_img = out_dir / "img" / "profile.jpg"
    assert copied_img.is_file()

    html = (out_dir / "html" / "tmp.html").read_text()
    assert "../img/profile.jpg" in html
