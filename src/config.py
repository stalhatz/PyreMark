import tomllib
import argparse
from enum import Enum
import logging
import os

from types import SimpleNamespace
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)
FORMAT = '[%(funcName)s] : %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


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
    intermediate_dir: str = "./output"
    data_root: str | None = None


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
    for (k, v) in top.items():
        # We may overwrite
        if v is not None:
            output[k] = v
        # We don't want to overwrite l, only propagate None keys
        if v is None and k not in output:
            output[k] = None
    return output


def parse_cli_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns: argparse.Namespace with all CLI flag values.
    """
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

    parser.add_argument("--intermediate-dir", default=None,
                        help="Directory for intermediate build artifacts (html/, css/, js/, img/ subdirs). Defaults to the current directory.")

    parser.add_argument("--data-root", default=None,
                        help="Root directory for resolving relative paths in TOML and YAML files")

    return parser.parse_args()


def load_toml_config(path: str) -> dict:
    """Load a TOML configuration file.

    path: path to the .toml file.

    Returns: parsed dictionary.
    """
    with open(path, "rb") as fd:
        return tomllib.load(fd)


def overlay_args(toml_config: dict, cli_args_dict: dict) -> SimpleNamespace:
    """Merge TOML configuration with CLI arguments.

    toml_config: parsed TOML dictionary (lower priority).
    cli_args_dict: CLI arguments dictionary (higher priority, overwrites TOML).

    Returns: SimpleNamespace with merged values.
    """
    args = overlay(toml_config, cli_args_dict)
    return SimpleNamespace(**args)


def resolve_build_config(args: SimpleNamespace | argparse.Namespace, yaml_files: list[str] | None = None,
                         config_file_path: str | None = None) -> BuildConfig:
    """Validate CLI arguments and resolve templates, theme, and output paths.

    args: parsed CLI arguments or merged TOML+CLI namespace.
    yaml_files: list of YAML file paths to use (overrides args.yaml).
    config_file_path: path to the TOML config file, if one was used.

    Returns: populated BuildConfig.

    Raises:
        ValueError: on invalid argument combinations or missing required args.
    """
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
        if getattr(args, "type", None) is None:
            raise ValueError(
                "Document type not specified. The referenced TOML config must have a "
                "'type' field (e.g. type = 'cv' or type = 'coverletter'), or use --type flag."
            )

    if template is None:
        raise ValueError("No html template provided")

    # data_root resolution (priority: CLI > TOML > auto-detect > CWD)
    data_root = getattr(args, "data_root", None)
    if data_root is not None and config_file_path is not None:
        data_root = os.path.join(os.path.dirname(os.path.abspath(config_file_path)),
                                  data_root)
        data_root = os.path.abspath(data_root)
    elif data_root is not None:
        data_root = os.path.abspath(data_root)
    elif config_file_path is not None:
        data_root = os.path.dirname(os.path.abspath(config_file_path))
    else:
        data_root = os.path.abspath(os.getcwd())

    # Resolve yaml_files against data_root
    if yaml_files is not None:
        resolved = []
        for f in yaml_files:
            if os.path.isabs(f):
                resolved.append(f)
            else:
                resolved.append(os.path.normpath(os.path.join(data_root, f)))
        yaml_files = resolved

    cfg = dict(
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
        data_root=data_root,
    )
    intermediate_dir = getattr(args, "intermediate_dir", None)
    if intermediate_dir is not None:
        cfg["intermediate_dir"] = intermediate_dir
    return BuildConfig(**cfg)


def setup_logging(verbose: str) -> None:
    """Set the logging level from a string.

    verbose: one of "info", "debug", or "warn".

    Side-effects: reconfigures the root logger level.
    """
    if verbose == "info":
        logging.basicConfig(level=logging.INFO)
    elif verbose == "debug":
        logging.basicConfig(level=logging.DEBUG)
    elif verbose == "warn":
        logging.basicConfig(level=logging.WARN)
