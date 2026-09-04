"""Subprocess helpers shared by every automation."""

import subprocess
from pathlib import Path

from automation import AutomationError


def run(*args: str, cwd: Path | None = None) -> str:
    """Run a command, return its stripped stdout, raise AutomationError with stderr on failure."""
    try:
        result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if isinstance(e.stderr, str) else ""
        raise AutomationError(f"`{' '.join(args)}` failed:\n{stderr}") from e
    return result.stdout.strip()


def git_root(cwd: Path | None = None) -> Path:
    try:
        return Path(run("git", "rev-parse", "--show-toplevel", cwd=cwd))
    except AutomationError as e:
        raise AutomationError("run inside the dotfiles repository") from e
