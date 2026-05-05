import pytest
import sys
from pathlib import Path

from copy import deepcopy

test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir.parent))

from src.data import yearInDateString

def test_yearInDateString_one_date():
    assert yearInDateString("Hello_World_2030") == "2030"
def test_yearInDateString_two_dates():
    assert yearInDateString("Hello_2033World_2031") == "2033"
def test_yearInDateString_consecutive_numbers():
    assert yearInDateString("Hello_2032031") == "2032"
def test_yearInDateString_no_numbers():
    assert yearInDateString("Hello_World") is None

from src.data import findDateField
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

from src.data import sortDict
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

from src.data import sortData
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

from src.theme import ThemeResolver, ThemeLoader

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
            sys.executable, "-m", "src.main",
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
            sys.executable, "-m", "src.main",
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
            sys.executable, "-m", "src.main",
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
            sys.executable, "-m", "src.main",
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
            sys.executable, "-m", "src.main",
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
            sys.executable, "-m", "src.main",
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
            sys.executable, "-m", "src.main",
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

from src.config import resolve_build_config
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
            sys.executable, "-m", "src.main",
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
            sys.executable, "-m", "src.main",
            "--cv", str(toml_file),
            "--output", str(tmp_path / "out.pdf"),
            "--intermediate-dir", str(tmp_path),
        ],
        capture_output=True, text=True
    )
    assert "no yaml/ directory found" in result.stdout or "no yaml/ directory found" in result.stderr


def test_resolve_user_images_copies_and_rewrites(tmp_path):
    """resolve_user_images should copy image and rewrite path to ../img/<name>."""
    from src.images import resolve_user_images

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
    from src.images import resolve_user_images

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
    from src.images import resolve_user_images

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
            sys.executable, "-m", "src.main",
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


# Branch analysis for deep_merge:
# 1. Branch tree:
#    if isinstance(d1, dict) and isinstance(d2, dict)  → recursive merge of shared keys
#      (shared keys: d1[k]==d2[k] → keep, else deep_merge recursively)
#    elif not replace → flatten both into list  [*listify(d1), *listify(d2)]
#    else → return d2
# 2. Input domain: dicts, non-dicts, lists, scalars, nested, empty dicts; replace=True/False
# 3. Call sites: readYamlData (replace=False, merges parsed YAML into accumulator);
#    load_and_merge_data (replace=True, merges data_override on top of yaml_data)
# 4. Contract: Recursively merge two dicts, bundling conflicting leaf values into lists
#    unless replace=True (then d2 wins).

from src.data import deep_merge, tr
from src.config import overlay

class TestDeepMerge:
    @pytest.mark.parametrize("d1,d2,replace,expected", [
        ({"a": 1}, {"b": 2}, False, {"a": 1, "b": 2}),
        ({"a": 1}, {"a": 1}, False, {"a": 1}),
        ({"a": {"x": 1}}, {"a": {"y": 2}}, False, {"a": {"x": 1, "y": 2}}),
        ({"a": 1}, {"a": 2}, False, {"a": [1, 2]}),
        ({"a": 1}, {"a": 2}, True, {"a": 2}),
        ({"a": [1]}, {"a": 2}, False, {"a": [1, 2]}),
        (1, 2, False, [1, 2]),
        (1, 2, True, 2),
        (1, [2], False, [1, 2]),
        ({}, {}, False, {}),
        ({"a": {"b": {"c": 1}}}, {"a": {"b": {"d": 2}}}, False,
         {"a": {"b": {"c": 1, "d": 2}}}),
        ({"a": {"x": 1, "y": 2}, "b": [1, 2]}, {"a": {"x": 99}, "c": 3}, True,
         {"a": {"x": 99, "y": 2}, "b": [1, 2], "c": 3}),
    ])
    def test_deep_merge(self, d1, d2, replace, expected):
        assert deep_merge(d1, d2, replace) == expected


# Branch analysis for tr:
# 1. Branch tree:
#    if isinstance(prop, dict):
#      if lang is not None and lang in prop → return prop[lang]
#      elif "def" in prop → return prop["def"]
#      else → return default
#    else:
#      if prop is not None → return prop
#      else → return default
# 2. Input domain: prop=dict|str|None, lang=str|None, default=any|None
# 3. Call sites: createQRCode — tr(linkSection, lang) where linkSection = section.get("link")
# 4. Contract: Returns i18n version of property — prop[lang], prop["def"], or default if neither.

class TestTr:
    @pytest.mark.parametrize("prop,lang,default,expected", [
        ({"en": "hello", "fr": "bonjour"}, "en", None, "hello"),
        ({"en": "hello", "def": "bonjour"}, "fr", None, "bonjour"),
        ({"en": "hello"}, None, None, None),
        ({"en": "hello"}, None, "n/a", "n/a"),
        ("hello", "en", None, "hello"),
        (None, "en", "fallback", "fallback"),
        (None, "en", None, None),
        ({"def": "default_val"}, None, None, "default_val"),
        ({"def": "default_val"}, "en", None, "default_val"),
    ])
    def test_tr(self, prop, lang, default, expected):
        assert tr(prop, lang, default) == expected


# Branch analysis for overlay:
# 1. Branch tree:
#    for (k,v) in top.items():
#      if v is not None → output[k] = v
#      if v is None and k not in output → output[k] = None
# 2. Input domain: two dicts, None values in top; keys in one/both/neither
# 3. Call sites: overlay_args(toml_config, cli_args_dict) — CLI args overlay TOML config
# 4. Contract: Shallow merge — top overrides base; None in top does NOT erase base key,
#    but propagates for missing keys. Base is not mutated.

class TestOverlay:
    def test_new_keys_from_top(self):
        assert overlay({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_top_overwrites(self):
        assert overlay({"a": 1}, {"a": 2}) == {"a": 2}

    def test_none_does_not_overwrite(self):
        assert overlay({"a": 1}, {"a": None}) == {"a": 1}

    def test_none_propagated_for_missing_key(self):
        assert overlay({}, {"a": None}) == {"a": None}

    def test_mixed(self):
        assert overlay({"a": 1, "b": 2}, {"b": None, "c": 3}) == {"a": 1, "b": 2, "c": 3}

    def test_both_empty(self):
        assert overlay({}, {}) == {}

    def test_no_top_keys(self):
        assert overlay({"a": 1}, {}) == {"a": 1}

    def test_base_unmodified(self):
        base = {"a": 1}
        result = overlay(base, {"b": 2})
        assert base == {"a": 1}
        assert result is not base


# Branch analysis for readYamlData:
# 1. Branch tree:
#    if any file doesn't end with .yaml → raise ValueError
#    for each yamlFile → yaml.safe_load + deep_merge(data, parsed, replace=False)
#    return data
# 2. Input domain: list of .yaml paths (single, multiple, empty); non-.yaml paths;
#    valid/invalid yaml content; empty yaml file
# 3. Call sites: load_and_merge_data(config.yaml_files) — passes list of resolved yaml paths
# 4. Contract: Read and merge YAML files left-to-right via deep_merge (replace=False).

from src.data import readYamlData
import yaml

def test_read_yaml_data_single_file(tmp_yaml_file):
    path = tmp_yaml_file({"name": "Test"}, "single.yaml")
    result = readYamlData([str(path)])
    assert result == {"name": "Test"}

def test_read_yaml_data_multi_file_disjoint(tmp_yaml_file):
    p1 = tmp_yaml_file({"a": 1}, "a.yaml")
    p2 = tmp_yaml_file({"b": 2}, "b.yaml")
    result = readYamlData([str(p1), str(p2)])
    assert result == {"a": 1, "b": 2}

def test_read_yaml_data_multi_file_overlap(tmp_yaml_file):
    p1 = tmp_yaml_file({"a": 1}, "a.yaml")
    p2 = tmp_yaml_file({"a": 2}, "b.yaml")
    result = readYamlData([str(p1), str(p2)])
    assert result == {"a": [1, 2]}

def test_read_yaml_data_txt_rejected(tmp_path):
    txt = tmp_path / "data.txt"
    txt.write_text("hello")
    with pytest.raises(ValueError, match="Expected only .yaml"):
        readYamlData([str(txt)])

def test_read_yaml_data_empty_yaml(tmp_yaml_file):
    path = tmp_yaml_file({}, "empty.yaml")
    result = readYamlData([str(path)])
    assert result == {}

def test_read_yaml_data_invalid_yaml(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text(": invalid yaml\n")
    with pytest.raises(yaml.YAMLError):
        readYamlData([str(f)])


# Branch analysis for renderTemplateAndWriteToFile:
# 1. Branch tree:
#    if template_filename is None → raise ValueError
#    if search_paths is None → defaults to ["."]
#    ThemeLoader(…), env.get_template(…), template.render(data), write to output
# 2. Input domain: template_filename=str|None|"", data=dict, output_filename=str,
#    search_paths=list[str]|None
# 3. Call sites: __main__ block — css, js, and html template rendering with ThemeResolver paths
# 4. Contract: Load jinja2 template from search_paths, render with data, write to output_filename.
#    Raises ValueError for None template, TemplateNotFound for missing/unfound template.

from src.rendering import renderTemplateAndWriteToFile
from jinja2 import TemplateNotFound as JinjaTemplateNotFound

def test_render_template_basic(tmp_jinja2_template, tmp_path):
    tmpl = tmp_jinja2_template("Hello {{ name }}", "greet.j2")
    output = tmp_path / "out.txt"
    renderTemplateAndWriteToFile("greet.j2", {"name": "world"}, str(output), [str(tmp_path)])
    assert output.read_text() == "Hello world"

def test_render_template_not_found(tmp_path):
    output = tmp_path / "out.txt"
    with pytest.raises(JinjaTemplateNotFound):
        renderTemplateAndWriteToFile("nonexistent.j2", {}, str(output), [str(tmp_path)])

def test_render_template_default_search_paths(tmp_path):
    """When search_paths is None, defaults to ["."]."""
    output = tmp_path / "out.txt"
    with pytest.raises(JinjaTemplateNotFound):
        renderTemplateAndWriteToFile("nonexistent_xyz.j2", {}, str(output))

def test_render_template_multi_path_first_wins(tmp_path):
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    dir1.mkdir()
    dir2.mkdir()
    (dir1 / "tmpl.j2").write_text("FIRST")
    (dir2 / "tmpl.j2").write_text("SECOND")
    output = tmp_path / "out.txt"
    renderTemplateAndWriteToFile("tmpl.j2", {}, str(output), [str(dir1), str(dir2)])
    assert output.read_text() == "FIRST"

def test_render_template_none_raises(tmp_path):
    output = tmp_path / "out.txt"
    with pytest.raises(ValueError, match="template_filename is required"):
        renderTemplateAndWriteToFile(None, {}, str(output))

def test_render_template_empty_string_raises(tmp_path):
    output = tmp_path / "out.txt"
    with pytest.raises(JinjaTemplateNotFound):
        renderTemplateAndWriteToFile("", {}, str(output), [str(tmp_path)])


# Branch analysis for generate_qr_code:
# 1. Branch tree: no conditionals — straight-line code
# 2. Input domain: url=str|None (None triggers AttributeError from qrcode/hashlib)
# 3. Call sites: createQRCode — generate_qr_code(link, output_path)
# 4. Contract: Generate a QR code PNG for url and save to output_path.

from src.images import generate_qr_code

def test_generate_qr_code_valid_url(tmp_path):
    output = tmp_path / "qr.png"
    generate_qr_code("https://example.com", str(output))
    assert output.exists()
    assert output.stat().st_size > 100

def test_generate_qr_code_empty_string(tmp_path):
    output = tmp_path / "qr.png"
    generate_qr_code("", str(output))
    assert output.exists()
    assert output.stat().st_size > 0

def test_generate_qr_code_none_raises(tmp_path):
    output = tmp_path / "qr.png"
    with pytest.raises(AttributeError):
        generate_qr_code(None, str(output))


# Branch analysis for createQRCode:
# 1. Branch tree:
#    for section_name in data["sections"]:
#      section = sections_data.get(section_name)
#      if isinstance(section, dict) and section.get("template") == "qr-code.html.j2":
#        link = tr(section.get("link"), lang)
#        if link: → hash url, generate QR, set section["qr_image"] = "../img/<filename>"
#        else: → log warning and skip
# 2. Input domain: data with/without qr sections; link as dict(str→str), plain str, or None;
#    multiple qr sections; lang present/missing in link dict
# 3. Call sites: __main__ — createQRCode(data, config.lang, img_dir)
# 4. Contract: Generates QR images for qr-code.html.j2 template sections; sets qr_image path.

from src.images import createQRCode

def test_create_qr_code_single_section_i18n_link(tmp_path):
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "qr_section": {
                "template": "qr-code.html.j2",
                "link": {"en": "https://example.com"},
            }
        },
        "sections": ["qr_section"],
    }
    createQRCode(data, "en", img_dir)
    qr_files = os.listdir(img_dir)
    assert len(qr_files) == 1
    assert qr_files[0].startswith("qr_")
    assert data["data"]["qr_section"]["qr_image"] == f"../img/{qr_files[0]}"

def test_create_qr_code_plain_string_link(tmp_path):
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "qr_section": {
                "template": "qr-code.html.j2",
                "link": "https://example.com",
            }
        },
        "sections": ["qr_section"],
    }
    createQRCode(data, "en", img_dir)
    qr_files = os.listdir(img_dir)
    assert len(qr_files) == 1
    assert data["data"]["qr_section"]["qr_image"].startswith("../img/")

def test_create_qr_code_i18n_fallback_skipped(tmp_path):
    """lang=fr with no 'fr' or 'def' in link dict → tr returns None → QR skipped."""
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "qr_section": {
                "template": "qr-code.html.j2",
                "link": {"en": "https://example.com"},
            }
        },
        "sections": ["qr_section"],
    }
    createQRCode(data, "fr", img_dir)
    assert len(os.listdir(img_dir)) == 0

def test_create_qr_code_no_qr_sections(tmp_path):
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "details": {"template": "preambule.html.j2", "name": "Test"},
        },
        "sections": ["details"],
    }
    createQRCode(data, "en", img_dir)
    assert len(os.listdir(img_dir)) == 0

def test_create_qr_code_missing_link_key(tmp_path):
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "qr_section": {
                "template": "qr-code.html.j2",
            }
        },
        "sections": ["qr_section"],
    }
    createQRCode(data, "en", img_dir)
    assert len(os.listdir(img_dir)) == 0

def test_create_qr_code_link_none(tmp_path):
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "qr_section": {
                "template": "qr-code.html.j2",
                "link": None,
            }
        },
        "sections": ["qr_section"],
    }
    createQRCode(data, "en", img_dir)
    assert len(os.listdir(img_dir)) == 0

def test_create_qr_code_img_prefix(tmp_path):
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "qr_section": {
                "template": "qr-code.html.j2",
                "link": "https://example.com",
            }
        },
        "sections": ["qr_section"],
    }
    createQRCode(data, "en", img_dir)
    assert data["data"]["qr_section"]["qr_image"].startswith("../img/")

def test_create_qr_code_multiple_sections(tmp_path):
    img_dir = str(tmp_path / "img")
    os.makedirs(img_dir)
    data = {
        "data": {
            "qr1": {
                "template": "qr-code.html.j2",
                "link": "https://example.com/a",
            },
            "qr2": {
                "template": "qr-code.html.j2",
                "link": "https://example.com/b",
            },
        },
        "sections": ["qr1", "qr2"],
    }
    createQRCode(data, "en", img_dir)
    qr_files = os.listdir(img_dir)
    assert len(qr_files) == 2
    assert data["data"]["qr1"]["qr_image"].startswith("../img/")
    assert data["data"]["qr2"]["qr_image"].startswith("../img/")
