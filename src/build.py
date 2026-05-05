import logging
import os
import hashlib
import qrcode
import shutil
import subprocess
import sys
import tempfile

from jinja2 import Environment, BaseLoader, TemplateNotFound
import yaml

from transform_md_to_yaml_html import transform_md_to_yaml_html
from os.path import join, exists, getmtime, dirname, abspath
from typing import Any
from collections.abc import Callable

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.config import (BuildConfig, load_toml_config, overlay_args, parse_cli_args,
                         resolve_build_config, setup_logging, overlay)


class ThemeLoader(BaseLoader):
    def __init__(self, search_paths: list[str]) -> None:
        """Load Jinja2 templates from an ordered list of search paths.

        search_paths: ordered list of directories to search for templates (first match wins).
        """
        self.search_paths = search_paths

    def get_source(self, environment: Environment, template: str) -> tuple[str, str, Callable[[], bool]]:
        """Resolve a template name to its source, path, and uptodate callback.

        environment: the Jinja2 environment (unused, required by BaseLoader interface).
        template: name of the template file to resolve.

        Returns: tuple of (source string, resolved path, uptodate callback).

        Raises:
            TemplateNotFound: if template is not found in any search path.
        """
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
        """Resolve theme paths, manifest, and search order for a named theme.

        theme_name: name of the theme directory under themes/.
        user_theme_dir: optional per-project theme directory for overrides.
        pre_styles: path to a CSS file to prepend to compiled CSS.
        post_styles: path to a CSS file to append to compiled CSS.

        Raises:
            ValueError: if the theme directory does not exist.
        """
        self.theme_name = theme_name
        self.user_theme_dir = user_theme_dir
        self.pre_styles_path = pre_styles
        self.post_styles_path = post_styles
        self._theme_root = join(dirname(abspath(__file__)), "..", "themes", theme_name)
        if not exists(self._theme_root):
            raise ValueError(f"Theme '{theme_name}' not found at {self._theme_root}")
        self._manifest = self._load_manifest()
        self._search_paths = self._build_search_paths()
        self._image_search_paths = self._build_image_search_paths()

    def search_paths(self) -> list[str]:
        """Ordered list of j2/ directories for template resolution.
        First match wins — equivalent to highest priority.
        """
        return list(self._search_paths)

    def image_search_paths(self) -> list[str]:
        """Ordered list of img/ directories for image resolution.
        First match wins — highest priority first.
        """
        return list(self._image_search_paths)

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
        """Read theme metadata from manifest.md as key-value pairs.

        Returns: dict of metadata parsed from markdown headers (e.g. "# theme: name").
        """
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
        """Build the ordered list of template search paths.

        Priority: user theme dir > this theme's j2/ > parent theme's paths (via extends chain).

        Returns: ordered list of directory paths for template resolution.
        """
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

    def _build_image_search_paths(self) -> list[str]:
        """Build the ordered list of image search paths.

        Priority: user theme img/ > this theme's img/ > parent theme's img/ (via extends chain).

        Returns: ordered list of directory paths for image resolution.
        """
        img_paths = []
        # 1. User theme_dir (highest priority)
        if self.user_theme_dir:
            user_img = join(self.user_theme_dir, "img")
            if exists(user_img):
                img_paths.append(user_img)

        # 2. This theme's img/
        this_img = join(self._theme_root, "img")
        if exists(this_img):
            img_paths.append(this_img)

        # 3. Walk extends: chain (parent themes) — lowest priority
        extends = self._manifest.get("extends")
        if extends:
            parent = ThemeResolver(extends, user_theme_dir=None,
                                   pre_styles=None, post_styles=None)
            img_paths.extend(parent.image_search_paths())

        return img_paths


def showHTML(htmlFile: str) -> None:
    """Open an HTML file in an external browser (Firefox).

    htmlFile: path to the HTML file to display.

    Side-effects: launches a Firefox browser process.
    """
    htmlViewerArgs = []
    htmlViewerArgs += ["firefox"]
    htmlViewerArgs += ["--private-window"]
    htmlViewerArgs += [htmlFile]
    logger.info(" ".join(htmlViewerArgs))
    result = subprocess.run(htmlViewerArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    logger.debug(result.stdout)
    logger.debug(result.stderr)


def viewPDF(pdfFile: str) -> None:
    """Open a PDF file in an external viewer (Okular).

    pdfFile: path to the PDF file to display.

    Side-effects: launches an Okular viewer process.
    """
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
    """Convert an HTML file to PDF using headless Chromium via Playwright.

    html_path: path to the input HTML file.
    output_path: path for the generated PDF file.

    Side-effects: launches a headless Chromium browser, writes a PDF to output_path.
    """

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
    """Recursively merge two dicts, bundling conflicting leaf values into lists.

    d1: lower-priority dictionary.
    d2: higher-priority dictionary.
    replace: if True, d2 values replace d1 values on conflict instead of bundling into a list.

    Returns: merged dict, or flattened list when both values are non-dicts.
    """
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
    """Render a Jinja2 template with data and write the result to a file.

    template_filename: name of the template to render (may use path components).
    data: dictionary to use for template variable substitution.
    output_filename: path for the rendered output file.
    search_paths: ordered list of directories to search for templates (defaults to ["."]).

    Raises:
        ValueError: if template_filename is None.
        TemplateNotFound: if the template cannot be found in any search path.

    Side-effects: writes rendered template to output_filename.
    """
    if template_filename is None:
        raise ValueError("template_filename is required")
    if template_filename == "":
        raise TemplateNotFound("")
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
    """Read and merge data from a list of YAML files, left to right.

    yamlFiles: list of paths to .yaml files.

    Returns: merged dictionary from all files.

    Raises:
        ValueError: if any file does not have a .yaml extension.
    """
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
    """Order a dictionary by applying a key function to its items.

    lines: dictionary to sort.
    dsc: True for descending order, False for ascending.
    key: unary function applied to each (k, v) item — return value is used for comparison.

    Returns: new dictionary with items in sorted order.
    """
    linesList = list(lines.items())
    linesList.sort(key=key,reverse = dsc)
    return dict(linesList)
    
# Sort data inplace
def sortData(data: Any, dsc: bool = False) -> None:
    """Recursively sort "lines" dicts within data by date, descending or ascending.

    data: nested dict structure (mutated in-place).
    dsc: True for descending order, False for ascending.

    Side-effects: mutates data by reordering "lines" dicts.
    """
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


def generate_qr_code(url: str, output_path: str) -> None:
    """Generate a QR code PNG image for a URL.

    url: URL the QR code will encode.
    output_path: path for the generated PNG file.

    Raises:
        AttributeError: if url is None.

    Side-effects: writes a PNG file to output_path.
    """
    if url is None:
        raise AttributeError("url is required")
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

def createQRCode(data: dict, lang: str, img_dir: str) -> None:
    """Generate QR code images for sections with template "qr-code.html.j2".

    data: the full data dictionary (mutated in-place).
    lang: language code for resolving multilingual link fields.
    img_dir: directory path to write QR code images into.

    Side-effects: writes PNG files to img_dir, mutates data by setting section["qr_image"].
    """
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
                output_path = os.path.join(img_dir, filename)
                generate_qr_code(link, output_path)
                # Relative path from html output to img directory
                section["qr_image"] = f"../img/{filename}"
                logger.info(f"Generated QR code for section '{section_name}': {filename}")
            else:
                logger.warning(f"QR section '{section_name}' missing 'link', skipping QR generation.")


def copy_theme_images(image_paths: list[str], output_img_dir: str) -> None:
    """Copy static theme images to the build output directory.

    Lower priority paths are copied first; higher priority paths overwrite.
    This applies the same overloading mechanism as template resolution.
    """
    for path in reversed(image_paths):
        if not exists(path):
            continue
        for filename in os.listdir(path):
            src = join(path, filename)
            if os.path.isfile(src):
                shutil.copy2(src, join(output_img_dir, filename))


_IMAGE_FIELDS = [
    (("data", "details"), "photo"),
    (("sender",), "signaturePhoto"),
]


def resolve_user_images(data: dict, data_root: str, img_dir: str) -> None:
    """Resolve user image paths against data_root, copy to build output, rewrite paths.

    data: the full data dictionary (mutated in-place).
    data_root: base directory for resolving relative image paths.
    img_dir: directory to copy resolved images into.

    Side-effects: copies image files to img_dir, mutates data by rewriting paths.
    """
    for dict_path, field in _IMAGE_FIELDS:
        d = data
        for key in dict_path:
            if isinstance(d, dict):
                d = d.get(key, {})
            else:
                d = {}
        if not isinstance(d, dict):
            continue
        value = d.get(field)
        if not value or not isinstance(value, str):
            continue
        if value.startswith("http://") or value.startswith("https://"):
            continue
        if os.path.isabs(value):
            continue

        resolved = os.path.join(data_root, value)
        resolved = os.path.abspath(resolved)
        dotpath = '.'.join(dict_path)
        if not os.path.exists(resolved):
            logger.warning(f"Image '{dotpath}.{field}': file '{resolved}' not found — keeping original path")
            continue
        if not os.path.isfile(resolved):
            logger.warning(f"Image '{dotpath}.{field}': path '{resolved}' is a directory — skipping")
            continue

        basename = os.path.basename(resolved)
        dest = os.path.join(img_dir, basename)
        shutil.copy2(resolved, dest)
        d[field] = f"../img/{basename}"
        logger.info(f"Resolved image '{dotpath}.{field}': {value!r} → {d[field]!r}")


def load_and_merge_data(yaml_files: list[str] | None, data_override: dict | None = None) -> dict:
    """Read YAML files, sort sections by date, and apply optional data override.

    yaml_files: list of YAML file paths (may be None).
    data_override: optional dict that overwrites matching keys in the merged data.

    Returns: the fully merged and sorted data dictionary.
    """
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
    """Ensure styles/script keys exist in data and set the lang field.

    data: the data dictionary (not mutated — a copy is returned).
    lang: language code to set as data["lang"].

    Returns: new dictionary with styles, script, and lang populated.
    """
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

    config = resolve_build_config(args, yaml_files=yaml_files,
                                  config_file_path=cli_args.cv if cli_args.cv else None)
    setup_logging(config.verbose)

    if config.data_root:
        if not os.path.isdir(config.data_root):
            logger.warning(f"data_root '{config.data_root}' does not exist")
        else:
            yaml_dir = os.path.join(config.data_root, "yaml")
            if not os.path.isdir(yaml_dir):
                logger.warning(f"data_root '{config.data_root}': no yaml/ directory found — are you sure this is the correct root?")

    data = load_and_merge_data(config.yaml_files, config.data_override)
    data = prepare_data(data, config.lang)

    idir = config.intermediate_dir
    html_dir = os.path.join(idir, "html")
    js_dir = os.path.join(idir, "js")
    css_dir = os.path.join(idir, "css")
    img_dir = os.path.join(idir, "img")

    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)

    htmlFile = os.path.join(html_dir, "tmp.html")

    search_paths = None
    if config.theme_active and config.theme is not None:
        resolver = ThemeResolver(config.theme, config.local_theming_dir, config.pre_styles, config.post_styles)
        search_paths = resolver.search_paths()
        logger.debug(f"Theme search paths: {search_paths}")

    if config.js_template:
        jsFile = os.path.join(js_dir, "tmp.js")
        renderTemplateAndWriteToFile(config.js_template, data, jsFile, search_paths)
        jsFile = os.path.relpath(jsFile, os.path.dirname(htmlFile))
        logger.debug(jsFile)
        if "script" in data:
            data["script"]["jsfile"] = jsFile

    if config.css_template:
        cssFile = os.path.join(css_dir, "styles.css")

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

    createQRCode(data, config.lang, img_dir)

    if config.theme_active and resolver is not None:
        copy_theme_images(resolver.image_search_paths(), img_dir)

    resolve_user_images(data, config.data_root, img_dir)

    renderTemplateAndWriteToFile(config.template, data, htmlFile, search_paths)

    if config.show == "html":
        showHTML(htmlFile)

    if config.output_name is not None:
        pdfFile = config.output_name
        asyncio.run(html_to_pdf_chromium(os.path.abspath(htmlFile), os.path.abspath(pdfFile)))
        if config.show == "pdf":
            viewPDF(pdfFile)
