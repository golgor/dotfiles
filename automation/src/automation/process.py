"""Subprocess helpers shared by every automation.

This is the only module that calls `subprocess`. The `nosemgrep` markers record that
the audit rule was checked, not bypassed. Both helpers take an argv sequence and
never use `shell=True`, so arguments reach the program verbatim and cannot become
extra commands. Callers keep program names and flags literal; the few values that come
from data (manifest `repo`/`commit`, release tags) are validated to shapes that cannot
be read as options, or are passed after `--` / in `refs/tags/` form.
"""

import subprocess
from pathlib import Path

from automation import AutomationError


def run(*args: str, cwd: Path | None = None) -> str:
    """Run a command, return its stripped stdout, raise AutomationError with stderr on failure."""
    try:
        # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
        result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.strip() if isinstance(e.stderr, str) else ""
        raise AutomationError(f"`{' '.join(args)}` failed:\n{stderr}") from e
    except OSError as e:  # executable missing from PATH, or not runnable
        raise AutomationError(f"cannot run `{args[0]}`: {e}") from e
    return result.stdout.strip()


def stream(*args: str, cwd: Path | None = None) -> int:
    """Run a command with its output going straight to the terminal; return the exit code."""
    try:
        # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
        return subprocess.run(args, cwd=cwd, check=False).returncode
    except OSError as e:
        raise AutomationError(f"cannot run `{args[0]}`: {e}") from e


def git_root(cwd: Path | None = None) -> Path:
    try:
        return Path(run("git", "rev-parse", "--show-toplevel", cwd=cwd))
    except AutomationError as e:
        raise AutomationError("run inside the dotfiles repository") from e
