"""omarchy/plugins.toml parsing: the shapes that reach argv, and typo protection."""

from pathlib import Path

import pytest

from automation import AutomationError
from automation.omarchy_plugins.manifest import Plugin, load_plugins


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "plugins.toml"
    path.write_text(text)
    return path


def test_parses_shared_and_host_scoped_plugins(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        """
[[plugin]]
id = "vt.sun"
git = "https://github.com/vitally/omarchy-solar-times.git"

[[plugin]]
id = "acme.trackpad"
git = "git@github.com:acme/trackpad.git"
hosts = ["golgor-framework"]
section = "right"
""",
    )

    assert load_plugins(path) == [
        Plugin("vt.sun", "https://github.com/vitally/omarchy-solar-times.git", (), None),
        Plugin("acme.trackpad", "git@github.com:acme/trackpad.git", ("golgor-framework",), "right"),
    ]


def test_plugin_without_hosts_applies_everywhere() -> None:
    shared = Plugin("a.b", "https://x/a.git", (), None)
    laptop = Plugin("c.d", "https://x/c.git", ("golgor-framework",), None)
    assert shared.for_host("golgor-pc")
    assert laptop.for_host("golgor-framework")
    assert not laptop.for_host("golgor-pc")


def test_empty_manifest_is_no_plugins(tmp_path: Path) -> None:
    assert load_plugins(write(tmp_path, "")) == []


@pytest.mark.parametrize(
    ("entry", "error"),
    [
        ('id = "-rf"\ngit = "https://x/a.git"', "id must"),
        ('id = "a.b"\ngit = "--upload-pack=evil"', "git must"),
        ('id = "a.b"\ngit = "file:///tmp/x"', "git must"),
        ('id = "a.b"\ngit = "https://x/a.git"\nsection = "middle"', "section must"),
        ('id = "a.b"\ngit = "https://x/a.git"\nhost = ["pc"]', "unknown key"),
        ('id = "a.b"\ngit = "https://x/a.git"\nhosts = "pc"', "hosts must"),
        ('git = "https://x/a.git"', "id must be a string"),
    ],
)
def test_rejects_invalid_entries(tmp_path: Path, entry: str, error: str) -> None:
    with pytest.raises(AutomationError, match=error):
        load_plugins(write(tmp_path, f"[[plugin]]\n{entry}\n"))


def test_rejects_duplicate_ids(tmp_path: Path) -> None:
    entry = '[[plugin]]\nid = "a.b"\ngit = "https://x/a.git"\n'
    with pytest.raises(AutomationError, match=r"listed twice: a\.b"):
        load_plugins(write(tmp_path, entry + entry))


def test_invalid_toml_and_missing_file_are_automation_errors(tmp_path: Path) -> None:
    with pytest.raises(AutomationError, match="invalid manifest"):
        load_plugins(write(tmp_path, "[[plugin]\n"))
    with pytest.raises(AutomationError, match="missing manifest"):
        load_plugins(tmp_path / "nope.toml")
