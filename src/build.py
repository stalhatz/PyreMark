import tomllib
import argparse
from enum import Enum
import logging
import os
import hashlib
import qrcode
from re import compile
import subprocess
import tempfile

from jinja2 import Environment, BaseLoader, TemplateNotFound
import yaml

from transform_md_to_yaml_html import transform_md_to_yaml_html
from os.path import join, exists, getmtime, dirname, abspath
from itertools import batched
from types import SimpleNamespace
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable


class ThemeLoader(BaseLoader):
    def __init__(self, search_paths: list[str]) -> None:
        self.search_paths = search_paths

    def get_source(self, environment: Environment, template: str) -> tuple[str, str, Callable[[], bool]]:
        for base in self.search_paths:
            path = join(base, template)
            if exists(path):
                mtime = getmtime(path)
                with open(path) as f:
                    source = f.read()
                return source, path, lambda: mtime == getmtime(path)
        raise TemplateNotFound(template)


class ThemeResolver:
    def __init__(self, theme_name: str, user_theme_dir: str | None = None,
                 pre_styles: str | None = None, post_styles: str | None = None) -> None:
        self.theme_name = theme_name
        self.user_theme_dir = user_theme_dir
        self.pre_styles_path = pre_styles
        self.post_styles_path = post_styles
        self._theme_root = join(dirname(abspath(__file__)), "..", "themes", theme_name)
        if not exists(self._theme_root):
            raise ValueError(f"Theme '{theme_name}' not found at {self._theme_root}")
        self._manifest = self._load_manifest()
        self._search_paths = self._build_search_paths()

    def search_paths(self) -> list[str]:
        """Ordered list of j2/ directories for template resolution.
        First match wins — equivalent to highest priority.
        """
        return list(self._search_paths)

    def get_pre_styles(self) -> str:
        """Content of pre-styles CSS, or empty string."""
        if self.pre_styles_path and exists(self.pre_styles_path):
            with open(self.pre_styles_path) as f:
                return f.read()
        return ""

    def get_post_styles(self) -> str:
        """Content of post-styles CSS, or empty string."""
        if self.post_styles_path and exists(self.post_styles_path):
            with open(self.post_styles_path) as f:
                return f.read()
        return ""

    def _load_manifest(self) -> dict:
        path = join(self._theme_root, "manifest.md")
        manifest = {}
        if exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    # Parse markdown headers like "# theme: name" as key-value pairs
                    if line.startswith("# ") and ":" in line:
                        line = line[2:]
                    elif line.startswith("#"):
                        continue
                    if ":" in line:
                        key, value = line.split(":", 1)
                        manifest[key.strip()] = value.strip()
        return manifest

    def _build_search_paths(self) -> list[str]:
        paths = []
        # 1. User theme_dir (highest priority)
        if self.user_theme_dir:
            user_j2 = join(self.user_theme_dir, "j2")
            if exists(user_j2):
                paths.append(user_j2)

        # 2. This theme's j2/
        paths.append(join(self._theme_root, "j2"))

        # 3. Walk extends: chain (parent themes)
        extends = self._manifest.get("extends")
        if extends:
            parent = ThemeResolver(extends, user_theme_dir=None,
                                   pre_styles=None, post_styles=None)
            paths.extend(parent.search_paths())

        return paths


class DocumentType(str, Enum):
    resume = 'resume'
    coverLetter = 'coverLetter'


@dataclass
class BuildConfig:
    theme: str | None = None
    local_theming_dir: str | None = None
    pre_styles: str | None = None
    post_styles: str | None = None
    theme_active: bool = False
    template: str | None = None
    css_template: str | None = None
    js_template: str | None = None
    yaml_files: list[str] | None = None
    lang: str = "en"
    output_name: str | None = None
    verbose: str = "info"
    show: str = "None"
    layout: dict | None = None
    styles: dict | None = None
    data_override: dict | None = None


def showHTML(htmlFile: str) -> None:
    '''
    Shows an html files using an external browser

    htmlFile: the path to the file to show
    '''
    htmlViewerArgs = []
    htmlViewerArgs += ["firefox"]
    htmlViewerArgs += [htmlFile]
    logger.info(" ".join(htmlViewerArgs))
    result = subprocess.run(htmlViewerArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)


def viewPDF(pdfFile: str) -> None:
    '''
    Shows a pdf file using an external program

    pdfFile: the path to the file to show
    '''
    pdfViewerArgs = []
    pdfViewerArgs += ["okular"]
    pdfViewerArgs += ["--unique"]
    pdfViewerArgs += [pdfFile]
    logger.info(" ".join(pdfViewerArgs))
    result = subprocess.run(pdfViewerArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)

import asyncio
from playwright.async_api import async_playwright

async def html_to_pdf_chromium(html_path: str, output_path: str) -> None:
    '''
    Creates a pdf file our of the contents of an html file

    html_path: path to html file
    output_path :  path to pdf file
    '''

    async with async_playwright() as p:
        # Launch Chromium (default)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Load local HTML file
        await page.goto(f'file://{html_path}', wait_until='networkidle')
        
        # Generate PDF with no margins
        await page.pdf(
            path=output_path,
            format='A4',
            margin={
                'top': '0mm',
                'right': '0mm',
                'bottom': '0mm',
                'left': '0mm'
            },
            print_background=True  # Include background colors/images
        )
        
        await browser.close()

# Copied from https://stackoverflow.com/a/50441142
def deep_merge(d1: Any, d2: Any, replace: bool = False) -> Any:
    '''
    Merges two dictionaries recursively while merging leaf values that correspond to the same key sequences into lists

    d1,d2: input dictionaries
    replace: controls whether we merge the two dictionaries leaf values or whether we replace the values by the values we find in d2 
    return : merged dictionary
    
    '''
    if isinstance(d1, dict) and isinstance(d2, dict):
        # Unwrap d1 and d2 in new dictionary to keep non-shared keys with **d1, **d2
        # Next unwrap a dict that treats shared keys
        # If two keys have an equal value, we take that value as new value
        # If the values are not equal, we recursively merge them
        return {
            **d1, **d2,
            **{k: d1[k] if d1[k] == d2[k] else deep_merge(d1[k], d2[k],replace)
            for k in {*d1} & {*d2}}
        }
    elif not replace:
        # This case happens when values are merged
        # It bundle values in a list, making sure
        # to flatten them if they are already lists
        return [
            *(d1 if isinstance(d1, list) else [d1]),
            *(d2 if isinstance(d2, list) else [d2])
        ]
    else:
        return d2

logger = logging.getLogger(__name__)
FORMAT = '[%(funcName)s] : %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def renderTemplateAndWriteToFile(template_filename: str | None, data: dict, output_filename: str, search_paths: list[str] | None = None) -> None:
    '''
    Renders a jinja2 template and places the result in an output file

    template_name: the name of the template to render
    data: the dictionary to use to render the template
    output_filename: the filename to output the rendered template
    search_paths: a list of paths (from most to least priority) to search for the template
    '''
    if template_filename is None:
        raise ValueError("template_filename is required")
    if search_paths is None:
        search_paths = ["."]
    logger.debug(f"Using template file : {template_filename}")
    loader = ThemeLoader(search_paths)
    env = Environment(loader=loader)
    template = env.get_template(template_filename)
    logger.debug(f"Merging template with data : {data}")
    rendered = template.render(data)
    with open(output_filename, "w") as hf:
        logger.info(f"Writing rendered template to {output_filename}")
        hf.write(rendered)

import re

def readYamlData(yamlFiles: list[str]) -> dict:
    '''
    Reads data from a list of yaml files and merges them into a dictionary object

    yamlFiles: List containing yaml files
    '''
    if any( [ os.path.splitext(k)[1]!= ".yaml" for k in yamlFiles] ):
        nonYamlValues = filter(lambda x: os.path.splitext(x)[1]!= ".yaml" , yamlFiles)
        raise ValueError("Expected only .yaml files as input but was given : " + str(list(nonYamlValues)))
    logger.info("Received the following yaml files as input :" + str(yamlFiles))
    #Read yaml file
    data = {}
    for yamlFile in yamlFiles:
        with open(yamlFile,"r") as yf:
            data = deep_merge(data,yaml.load(yf, Loader=yaml.SafeLoader))
    return data


def yearInDateString(s: str) -> str | None:
    '''
    return the year value contained in a string

    s: the string to get the year value from
    return : year value or None if no such value in s
    '''
    matches = re.findall(r'\d{4}', s)
    if len(matches) == 0:
        return None
    else:
        return matches[0]

def findDateField(x: Any) -> int | None:
    '''
    Find the date/year corresponding to a record

    x: the record
    returns : corresponding date/year to x, or None if no year found
    '''
    d = x[1]["date"]
    # First element without caring about key should give the date
    if type(d) is dict:
        dateString = list(d.items())[0][1]
    else:
        dateString = d
    year_str = yearInDateString(dateString)
    if year_str is None:
        return None
    return int(year_str)

# The argument of this funciton should be a dictionary with elements that need to be sorted 
# since a dictionary maintains order of iterms since Python 3.6
def sortDict(lines: dict, dsc: bool, key: Callable[[Any], Any]) -> dict:
    '''
    Orders a dictionary based on some key
    
    lines: the dictionary to sort
    dsc: descending (True) or ascending (False) order 
    key : unary function returning a number
    '''
    linesList = list(lines.items())
    linesList.sort(key=key,reverse = dsc)
    return dict(linesList)
    
# Sort data inplace
def sortData(data: Any, dsc: bool = False) -> None:
    # Find all lines
    if type(data) is dict:
        for k in data.keys():
            if k == "lines":
                if type(data["lines"]) is dict:
                    try:
                        data["lines"] = sortDict(data["lines"],dsc,findDateField)
                    except (TypeError,KeyError):
                        pass
            else:
                sortData(data[k],dsc)


def overlay(base: dict, top: dict) -> dict:
    """
    Shallow merge of two dicts where *top* takes precedence.
    - A key in *top* with a non-None value overwrites the same key in *base*.
    - A key in *top* with value None is treated as "not specified" and
      does NOT erase an existing value in *base* (it only fills a missing key).
    - Keys only in *base* are preserved unchanged.

    This is a *shallow* merge: nested dicts in *top* replace the entire
    value in *base*, they are not merged recursively.  If deep merge of
    nested dicts is needed, the ``n[k] = v`` branch should call
    ``deep_merge(base[k], v, replace=True)`` when both values are dicts.

    base : The lower‑priority dictionary.
    top :  The higher‑priority dictionary.
    returns : a new dictionary (shallow copy of *base* with *top* overlaid).
    """
    output = base.copy()
    for (k,v) in top.items():
        # We may overwrite
        if v is not None:
            output[k] = v
        # We don't want to overwrite l, only propagate None keys
        if v is None and k not in output:
            output[k] = None
    return output

def generate_qr_code(url: str, output_path: str) -> None:
    """
    Generate a QR code image for the given URL and save to output_path.
    
    url: URL the qrcode will be pointing to
    output_path: path to the file to save the qrcode into
    
    """
    qr = qrcode.QRCode(
        version=3,
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # pyright: ignore[reportAttributeAccessIssue]
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)  # pyright: ignore[reportArgumentType]
    logger.debug(f"Generated QR code for {url} at {output_path}")

def tr(prop: Any, lang: str | None = None, default: Any = None) -> Any:
    '''
    Returns the i18n version of a dictionary property

    returns prop or prop[lang] or prop['def'] or default if no such values exist
    '''
    if isinstance(prop, dict):
        if lang is not None and lang in prop:
            return prop[lang]
        elif "def" in prop:
            return prop["def"]
        else:
            return default
    else:
        if prop is not None:
            return prop
        else:
            return default

def createQRCode(data: dict, lang: str, path: str) -> None:
    '''
    Creates a qrcode in image file format corresponding to qrcode sections defined in the data

    data: the dictionary used to render all templates
    lang: the language we are targeting
    path: path to the output directory
    '''
    # Access the nested data dict where sections are stored
    sections_data = data.get("data", {})
    for section_name in data.get("sections", []):
        section = sections_data.get(section_name)
        if isinstance(section, dict) and section.get("template") == "qr-code.html.j2":
            linkSection = section.get("link")
            link = tr(linkSection,lang)
            if link:
                url_hash = hashlib.sha256(link.encode()).hexdigest()[:16]
                filename = f"qr_{url_hash}.png"
                output_path = os.path.join(path, filename)
                generate_qr_code(link, output_path)
                # Relative path from html output to img directory
                section["qr_image"] = f"../img/{filename}"
                logger.info(f"Generated QR code for section '{section_name}': {filename}")
            else:
                logger.warning(f"QR section '{section_name}' missing 'link', skipping QR generation.")



def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments and return the resulting namespace."""
    parser = argparse.ArgumentParser()

    parser.add_argument("--cv", help=".toml file containing a configuration to create a cv. Parameters specified via cli argument take precedence in order to easily tweek a configuration file.")
    parser.add_argument("-m","--md", help=".md file containing data and metadata for creating the document")
    parser.add_argument("-y","--yaml", help="(a series of) .yaml file(s) containing data for creating the document",nargs='+')
    parser.add_argument("--type",help="The type of document required. This is mutually exclusive with --template and --css.",choices = ["coverletter","CV"])
    parser.add_argument("--layout",help="String with dictionary values to define layout and customize the default template", nargs='+')
    parser.add_argument("--metadata",help="Extra metadata")
    parser.add_argument("--template",help="the html jinja2 template (.j2) to be customized.")
    parser.add_argument("-c","--css",help="the css jinja2 template (.j2) to be customized.")
    parser.add_argument("-j","--js",help="the js jinja2 template (.j2) to be customized.")
    parser.add_argument("-l","--lang",help="language to be used for the output document. Defaults to English", default=None)
    parser.add_argument("-o","--output",help="location of the output file. A .pdf suffix will be added if not already present in the filename")
    parser.add_argument("-s","--show",help="Show rendered html pdf or None",default= "None",choices=["pdf","html","None"])

    parser.add_argument("-v","--verbose",help="set to one of warn, info , debug",default="info", choices=["info","warn","debug"])

    # Theme-related CLI flags
    parser.add_argument("--theme", help="Named theme to use for rendering")
    parser.add_argument("--local-theming-dir", help="User theme directory for per-project overrides")
    parser.add_argument("--theme-pre-styles", help="CSS file to prepend to compiled CSS")
    parser.add_argument("--theme-post-styles", help="CSS file to append to compiled CSS")

    return parser.parse_args()


def load_toml_config(path: str) -> dict:
    """Load a TOML configuration file and return the parsed dict."""
    with open(path, "rb") as fd:
        return tomllib.load(fd)


def overlay_args(toml_config: dict, cli_args_dict: dict) -> SimpleNamespace:
    """Merge TOML config with CLI args (CLI takes precedence) and return as SimpleNamespace."""
    args = overlay(toml_config, cli_args_dict)
    return SimpleNamespace(**args)


def resolve_build_config(args: SimpleNamespace | argparse.Namespace, yaml_files: list[str] | None = None) -> BuildConfig:
    """Validate arguments, resolve templates/theme, and return a BuildConfig.
    Raises ValueError on invalid combinations or missing required args."""
    theme = getattr(args, "theme", None)
    local_theming_dir = getattr(args, "local_theming_dir", None)
    pre_styles = getattr(args, "theme_pre_styles", None)
    post_styles = getattr(args, "theme_post_styles", None)

    template = getattr(args, "template", None)
    css = getattr(args, "css", None)
    js = getattr(args, "js", None)

    output_name = getattr(args, "output", None)
    lang = getattr(args, "lang", None) or "en"
    verbose = getattr(args, "verbose", "info")
    show = getattr(args, "show", "None")
    layout = getattr(args, "layout", None)
    styles = getattr(args, "styles", None)

    has_type = getattr(args, "type", None) is not None
    has_theme = theme is not None
    theme_active = False

    if has_type:
        if template is not None:
            raise ValueError("--template is mutually exclusive with --type")
        if str.lower(args.type) == "cv":
            theme = theme or "default_cv"
            template = "resume.html.j2"
            if css is None:
                css = "styles.css.j2"
            if js is None:
                js = "scripts.js.j2"
            theme_active = True
        if args.type == "coverletter":
            theme = theme or "default_cover_letter"
            template = "cover_letter.html.j2"
            if css is None:
                css = "cover_letter.css.j2"
            theme_active = True
    elif has_theme:
        template = template or "resume.html.j2"
        if css is None:
            css = "styles.css.j2"
        if js is None:
            js = "scripts.js.j2"
        theme_active = True

    theming_options = getattr(args, "theming_options", None)
    if isinstance(theming_options, dict):
        if pre_styles is None:
            pre_styles = theming_options.get("pre_styles")
        if post_styles is None:
            post_styles = theming_options.get("post_styles")
        if local_theming_dir is None:
            local_theming_dir = theming_options.get("local_theming_dir")

    md = getattr(args, "md", None)
    if md is not None:
        if os.path.splitext(md)[1] != ".md":
            raise ValueError("Expected a .md file as input")
        if yaml_files is not None and getattr(args, "yaml", None) is not None:
            raise ValueError("Args --yaml and --md are incompatible")
        theme = theme or "default_cover_letter"
        template = "cover_letter.html.j2"
        if css is None:
            css = "cover_letter.css.j2"

    if template is None:
        raise ValueError("No html template provided")

    return BuildConfig(
        theme=theme,
        local_theming_dir=local_theming_dir,
        pre_styles=pre_styles,
        post_styles=post_styles,
        theme_active=theme_active,
        template=template,
        css_template=css,
        js_template=js,
        yaml_files=yaml_files,
        lang=lang,
        output_name=output_name,
        verbose=verbose,
        show=show,
        layout=layout,
        styles=styles,
        data_override=getattr(args, "data", None),
    )


def setup_logging(verbose: str) -> None:
    """Set logging level from a string: info, debug, or warn."""
    if verbose == "info":
        logging.basicConfig(level=logging.INFO)
    elif verbose == "debug":
        logging.basicConfig(level=logging.DEBUG)
    elif verbose == "warn":
        logging.basicConfig(level=logging.WARN)


def load_and_merge_data(yaml_files: list[str] | None, data_override: dict | None = None) -> dict:
    """Read YAML files, sort data, merge with optional TOML data override."""
    data = {}
    if yaml_files is not None:
        data = readYamlData(yaml_files)
    sortData(data, True)
    yaml_data = data.get("data", {})
    if data_override is not None:
        yaml_data = deep_merge(yaml_data, data_override, replace=True)
    data["data"] = yaml_data
    return data


def prepare_data(data: dict, lang: str) -> dict:
    """Ensure styles/script keys exist and set the lang field."""
    if "styles" not in data:
        data["styles"] = {}
    if "script" not in data:
        data["script"] = {}
    data = dict(data)
    data["lang"] = lang
    return data


if __name__ == "__main__":
    cli_args = parse_cli_args()

    if cli_args.cv is not None:
        toml_config = load_toml_config(cli_args.cv)
        args = overlay_args(toml_config, vars(cli_args))
    else:
        args = cli_args

    yaml_files = None
    if args.md is not None:
        yaml_files = [tempfile.mkstemp(suffix=".yaml")[1]]
        logger.info(f"Using {yaml_files[0]} as temporary .yaml file")
        transform_md_to_yaml_html(args.md, yaml_files[0])
    elif getattr(args, "yaml", None) is not None:
        yaml_files = args.yaml

    config = resolve_build_config(args, yaml_files=yaml_files)
    setup_logging(config.verbose)

    data = load_and_merge_data(config.yaml_files, config.data_override)
    data = prepare_data(data, config.lang)

    htmlFile = "./html/tmp.html"

    search_paths = None
    if config.theme_active and config.theme is not None:
        resolver = ThemeResolver(config.theme, config.local_theming_dir, config.pre_styles, config.post_styles)
        search_paths = resolver.search_paths()
        logger.debug(f"Theme search paths: {search_paths}")

    if config.js_template:
        jsFile = "./js/tmp.js"
        renderTemplateAndWriteToFile(config.js_template, data, jsFile, search_paths)
        jsFile = os.path.relpath(jsFile, os.path.dirname(htmlFile))
        logger.debug(jsFile)
        if "script" in data:
            data["script"]["jsfile"] = jsFile

    if config.css_template:
        cssFile = "./css/styles.css"

        if config.styles is not None:
            if "styles" not in data:
                data["styles"] = {}
            for key in config.styles.keys():
                data["styles"][key] = config.styles[key]

        if config.theme_active and resolver is not None:
            renderTemplateAndWriteToFile(config.css_template, data, cssFile, search_paths)
            pre = resolver.get_pre_styles()
            post = resolver.get_post_styles()
            if pre or post:
                with open(cssFile, "r") as f:
                    css_core = f.read()
                with open(cssFile, "w") as f:
                    f.write(pre + css_core + post)
        else:
            renderTemplateAndWriteToFile(config.css_template, data, cssFile, search_paths)

        cssFile = os.path.relpath(cssFile, os.path.dirname(htmlFile))
        logger.debug(cssFile)
        if "styles" not in data:
            data["styles"] = {}
        data["styles"]["cssfile"] = cssFile

        if config.layout is not None and "sections" in config.layout:
            data["sections"] = config.layout["sections"]

    img_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'img'))
    os.makedirs(img_dir, exist_ok=True)
    createQRCode(data, config.lang, img_dir)

    renderTemplateAndWriteToFile(config.template, data, htmlFile, search_paths)

    if config.show == "html":
        showHTML(htmlFile)

    if config.output_name is not None:
        pdfFile = config.output_name
        asyncio.run(html_to_pdf_chromium(os.path.abspath(htmlFile), os.path.abspath(pdfFile)))
        if config.show == "pdf":
            viewPDF(pdfFile)
