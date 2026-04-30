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
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out.pdf").exists()
    # CSS should have the new theme's distinct styles
    css = Path("css/styles.css").read_text()
    assert "'Inter'" in css or "#2563eb" in css or "#eef2ff" in css


def test_ext_default_cv_example_override(tmp_path):
    """ext_default_cv_example should override photo.css with funky frame."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--theme", "ext_default_cv_example",
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = Path("css/styles.css").read_text()
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
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = Path("css/styles.css").read_text()
    assert css.startswith("/* pre_styles test")


def test_post_styles_inserted_at_end(tmp_path):
    """post_styles should appear at the end of compiled CSS."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/single_page.toml",
            "--theme-post-styles", "testdata/post.css",
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = Path("css/styles.css").read_text()
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
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    html = Path("html/tmp.html").read_text()
    assert "testdata-override" in html


def test_config_styles_tokens_override(tmp_path):
    """Config [styles] tokens should override CSS variables."""
    import subprocess
    result = subprocess.run(
        [
            sys.executable, "src/build.py",
            "--cv", "testdata/cv/tokens_tweaked.toml",
            "--output", str(tmp_path / "out.pdf"),
        ],
        capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    css = Path("css/styles.css").read_text()
    assert "--fontSize: 9.5px" in css
    assert "--fontFamily: 'Roboto', 'Helvetica', sans-serif" in css
