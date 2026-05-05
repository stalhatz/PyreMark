import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from src.config import (load_toml_config, overlay, overlay_args, parse_cli_args,
                        resolve_build_config, setup_logging)
from src.data import load_and_merge_data, prepare_data
from src.theme import ThemeResolver, copy_theme_images
from src.rendering import (renderTemplateAndWriteToFile, showHTML, viewPDF,
                            html_to_pdf_chromium)
from src.images import createQRCode, resolve_user_images
from src.transform_md_to_yaml_html import parse_markdown_config, body_to_data_dict

logger = logging.getLogger(__name__)
FORMAT = '[%(funcName)s] : %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


def main() -> None:
    cli_args = parse_cli_args()

    if cli_args.cv is not None:
        toml_config = load_toml_config(cli_args.cv)
        args = overlay_args(toml_config, vars(cli_args))
        config_file_path = cli_args.cv
    elif cli_args.md is not None:
        md_config = parse_markdown_config(cli_args.md)
        toml_config = load_toml_config(md_config["extends"])
        merged = overlay(toml_config, md_config.get("config") or {})
        args = overlay_args(merged, vars(cli_args))
        config_file_path = md_config["extends"]
    else:
        args = cli_args
        config_file_path = None

    yaml_files = getattr(args, "yaml", None)
    body_data = None
    frontmatter_data = None

    if cli_args.md is not None:
        yaml_files = toml_config.get("yaml", [])
        if cli_args.yaml is not None:
            yaml_files = list(cli_args.yaml)
        doc_type = str(getattr(args, "type", "cv")).lower()
        if doc_type != "cv":
            body_data = body_to_data_dict(md_config["body"])
        frontmatter_data = md_config.get("data")
    elif getattr(args, "yaml", None) is not None:
        yaml_files = args.yaml

    config = resolve_build_config(args, yaml_files=yaml_files,
                                  config_file_path=config_file_path)
    setup_logging(config.verbose)

    if config.data_root:
        if not os.path.isdir(config.data_root):
            logger.warning(f"data_root '{config.data_root}' does not exist")
        else:
            yaml_dir = os.path.join(config.data_root, "yaml")
            if not os.path.isdir(yaml_dir):
                logger.warning(f"data_root '{config.data_root}': no yaml/ directory found — are you sure this is the correct root?")

    data = load_and_merge_data(config.yaml_files, config.data_override,
                              body_data, frontmatter_data)
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


if __name__ == "__main__":
    main()
