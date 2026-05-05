import logging
import os
import shutil

from os.path import join, exists, getmtime, dirname, abspath
from collections.abc import Callable
from jinja2 import BaseLoader, Environment, TemplateNotFound

logger = logging.getLogger(__name__)


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
