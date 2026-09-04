"""Python automation for the dotfiles repository.

Each subpackage is one automation with a `cli.py` entry point wired up in
pyproject.toml `[project.scripts]` and invoked from a mise task.
"""


class AutomationError(Exception):
    """A failure to report to the user and exit 1 on. Library code raises it; CLIs catch it."""
