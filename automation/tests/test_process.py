"""The shared subprocess helpers: the failure modes callers rely on."""

import pytest

from automation import AutomationError
from automation.process import run


def test_missing_executable_is_an_automation_error() -> None:
    with pytest.raises(AutomationError, match="cannot run `definitely-not-a-command`"):
        run("definitely-not-a-command")
