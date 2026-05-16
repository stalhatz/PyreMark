import logging
import subprocess

logger = logging.getLogger(__name__)


def is_git_repo(path: str) -> bool:
    """Check if a path is a git repository.

    path: filesystem path to check.

    Returns: True if path is a git repository, False otherwise.
    """
    result = subprocess.run(
        ["git", "-C", path, "rev-parse", "--git-dir"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def get_git_hash(path: str) -> str | None:
    """Get the full git commit hash for a repository.

    path: filesystem path to the repository.

    Returns: 40-character git hash on success, None if path is not a git repo.

    Side-effects: logs a warning if path is not a git repository.
    """
    if not is_git_repo(path):
        logger.warning(f"'{path}' is not a git repository — git hash will be omitted")
        return None
    result = subprocess.run(
        ["git", "-C", path, "rev-parse", "HEAD"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    logger.warning(f"Failed to get git hash for '{path}'")
    return None


def get_project_version() -> str:
    """Get the PyreMark project version.

    Returns: version string from package metadata, or fallback version.
    """
    try:
        from importlib.metadata import version
        return version("css-resume")
    except Exception:
        return "0.1.0"
