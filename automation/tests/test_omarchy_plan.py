"""plan(): which listed plugins this host is missing, and what is installed but unlisted."""

from automation.omarchy_plugins.manifest import Plugin
from automation.omarchy_plugins.plan import Plan, plan

SHARED = Plugin("vt.sun", "https://x/sun.git", (), None)
LAPTOP = Plugin("acme.trackpad", "https://x/trackpad.git", ("golgor-framework",), None)
PC = Plugin("acme.gpu", "https://x/gpu.git", ("golgor-pc",), None)


def test_missing_plugins_for_this_host_are_installed() -> None:
    result = plan([SHARED, LAPTOP, PC], "golgor-framework", installed=set())
    assert result == Plan(install=[SHARED, LAPTOP], present=[], unmanaged=[])


def test_installed_plugins_are_left_alone() -> None:
    result = plan([SHARED, LAPTOP], "golgor-framework", installed={"vt.sun"})
    assert result == Plan(install=[LAPTOP], present=[SHARED], unmanaged=[])


def test_unlisted_and_other_host_plugins_are_unmanaged() -> None:
    result = plan([SHARED, PC], "golgor-framework", installed={"vt.sun", "acme.gpu", "z.extra"})
    assert result == Plan(install=[], present=[SHARED], unmanaged=["acme.gpu", "z.extra"])
