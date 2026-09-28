"""`omarchy-plugins sync` through run_sync() with a fake host, plus OmarchyHost on real dirs."""

import io
from dataclasses import dataclass, field
from pathlib import Path

from automation import AutomationError
from automation.omarchy_plugins.cli import run_sync
from automation.omarchy_plugins.host import OmarchyHost
from automation.omarchy_plugins.manifest import MANIFEST, Plugin
from tests.helpers import git

MANIFEST_TEXT = """
[[plugin]]
id = "vt.sun"
git = "https://x/sun.git"

[[plugin]]
id = "acme.broken"
git = "https://x/broken.git"

[[plugin]]
id = "acme.trackpad"
git = "https://x/trackpad.git"
hosts = ["golgor-framework"]
"""


@dataclass
class FakeHost:
    ids: set[str] = field(default_factory=set)
    origins: dict[str, str] = field(default_factory=dict)
    added: list[str] = field(default_factory=list)

    def installed(self) -> set[str]:
        return set(self.ids)

    def origin(self, plugin_id: str) -> str | None:
        return self.origins.get(plugin_id)

    def add(self, plugin: Plugin) -> None:
        if plugin.id == "acme.broken":
            raise AutomationError("clone failed")
        self.added.append(plugin.id)


def sync(tmp_path: Path, host: FakeHost, *, dry_run: bool = False) -> tuple[bool, str, str]:
    (tmp_path / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / MANIFEST).write_text(MANIFEST_TEXT)
    out, err = io.StringIO(), io.StringIO()
    ok = run_sync(tmp_path, "golgor-pc", host, dry_run=dry_run, out=out, err=err)
    return ok, out.getvalue(), err.getvalue()


def test_installs_missing_continues_past_failure_and_reports(tmp_path: Path) -> None:
    host = FakeHost(ids={"x.extra"}, origins={"x.extra": "https://x/extra.git"})

    ok, out, err = sync(tmp_path, host)

    assert not ok
    assert host.added == ["vt.sun"]  # broken failed, trackpad is laptop-only
    assert "installed  vt.sun" in out
    assert "unmanaged  x.extra  https://x/extra.git" in out
    assert "failed     acme.broken: clone failed" in err


def test_dry_run_changes_nothing(tmp_path: Path) -> None:
    host = FakeHost(ids={"vt.sun", "hancore.local"})

    ok, out, err = sync(tmp_path, host, dry_run=True)

    assert ok
    assert host.added == []
    assert "would install  acme.broken  https://x/broken.git" in out
    assert "present    vt.sun" in out
    assert "unmanaged  hancore.local  (no git origin)" in out
    assert err == ""


def test_up_to_date_host_succeeds(tmp_path: Path) -> None:
    ok, out, _ = sync(tmp_path, FakeHost(ids={"vt.sun", "acme.broken"}))
    assert ok
    assert "Nothing to install." in out


def test_omarchy_host_lists_plugin_dirs_and_git_origins(tmp_path: Path) -> None:
    (tmp_path / "vt.sun").mkdir()
    git("init", "-q", cwd=tmp_path / "vt.sun")
    git("remote", "add", "origin", "https://x/sun.git", cwd=tmp_path / "vt.sun")
    (tmp_path / "hancore.local").mkdir()
    (tmp_path / ".add.tmp.123").mkdir()  # omarchy's in-flight clone
    (tmp_path / "stray-file").write_text("")
    (tmp_path / "linked").symlink_to(tmp_path / "hancore.local")

    host = OmarchyHost(tmp_path)

    assert host.installed() == {"vt.sun", "hancore.local", "linked"}
    assert host.origin("vt.sun") == "https://x/sun.git"
    assert host.origin("hancore.local") is None
