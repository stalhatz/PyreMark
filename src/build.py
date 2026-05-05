import asyncio
import logging
import os
import hashlib
import qrcode
import shutil
import sys
import tempfile

from transform_md_to_yaml_html import transform_md_to_yaml_html

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.config import (BuildConfig, load_toml_config, overlay_args, parse_cli_args,
                         resolve_build_config, setup_logging, overlay)
from src.data import (deep_merge, tr, readYamlData, yearInDateString, findDateField,
                       sortDict, sortData, load_and_merge_data, prepare_data)
from src.theme import (ThemeLoader, ThemeResolver, copy_theme_images)
from src.rendering import (renderTemplateAndWriteToFile, showHTML, viewPDF,
                            html_to_pdf_chromium)

logger = logging.getLogger(__name__)
FORMAT = '[%(funcName)s] : %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

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
