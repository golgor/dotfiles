"""End-to-end through `update()` with a local tagged repo as the release source."""

import io
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills.cli import apply_dotfiles, build_parser, update
from automation.skills.manifest import load_manifest
from tests.helpers import Dotfiles, Upstream, write_skill


@dataclass
class Result:
    out: str
    err: str
    applied: bool


def run_update(dotfiles: Dotfiles, upstream: Upstream) -> Result:
    out, err, applied = io.StringIO(), io.StringIO(), []
    update(dotfiles.root, lambda _repo: upstream, applied.append, out, err)
    return Result(out.getvalue(), err.getvalue(), applied == [dotfiles.root])


def test_first_import_syncs_and_records(dotfiles: Dotfiles, upstream: Upstream) -> None:
    r = run_update(dotfiles, upstream)

    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text().endswith("# alpha v1\n")
    assert (dotfiles.root / "skills/common/alpha/agents/openai.yaml").exists()
    assert (dotfiles.root / "skills/common/beta/SKILL.md").exists()
    assert not (dotfiles.root / "skills/common/extra").exists()

    release = load_manifest(dotfiles.manifest).release
    assert release.tag == "v1.0.0" and len(release.commit) == 40
    assert "# header comment survives" in dotfiles.manifest.read_text()

    assert "No locked release yet" in r.out
    assert "Syncing 2 skills from v1.0.0" in r.out
    assert "not selected (1):\n  extra" in r.out
    assert r.applied
    assert r.err == ""


def test_second_run_is_a_noop(dotfiles: Dotfiles, upstream: Upstream) -> None:
    run_update(dotfiles, upstream)
    dotfiles.commit_all()

    r = run_update(dotfiles, upstream)
    assert "nothing to do" in r.out
    assert not r.applied


def test_newly_selected_skill_syncs_at_current_release(
    dotfiles: Dotfiles, upstream: Upstream
) -> None:
    run_update(dotfiles, upstream)
    dotfiles.commit_all()
    release = load_manifest(dotfiles.manifest).release
    dotfiles.write_manifest(
        common=["alpha", "beta"], claude=["extra"], tag=release.tag, commit=release.commit
    )

    r = run_update(dotfiles, upstream)

    assert "Syncing 3 skills" in r.out
    assert (dotfiles.root / "skills/claude/extra/SKILL.md").exists()
    assert "extra is Claude-only but mise.toml has no entry" in r.err


def test_deselected_skill_is_reported_as_orphan(dotfiles: Dotfiles, upstream: Upstream) -> None:
    run_update(dotfiles, upstream)
    dotfiles.commit_all()
    release = load_manifest(dotfiles.manifest).release
    dotfiles.write_manifest(common=["alpha"], tag=release.tag, commit=release.commit)

    r = run_update(dotfiles, upstream)

    assert "nothing to do" in r.out
    assert "warning: skills/common/beta matches an upstream skill but is not selected" in r.err
    assert (dotfiles.root / "skills/common/beta").exists()  # never deleted silently


def test_local_edit_blocks_update(dotfiles: Dotfiles, upstream: Upstream) -> None:
    run_update(dotfiles, upstream)
    (dotfiles.root / "skills/common/alpha/SKILL.md").write_text("forked!\n")
    dotfiles.commit_all("local fork")
    upstream.commit("v1.1.0", tag="v1.1.0")

    with pytest.raises(AutomationError, match="differs from locked release: skills/common/alpha"):
        run_update(dotfiles, upstream)
    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text() == "forked!\n"


def test_release_bump_deletes_removed_files_and_records(
    dotfiles: Dotfiles, upstream: Upstream
) -> None:
    run_update(dotfiles, upstream)
    dotfiles.commit_all()
    (upstream.path / "skills/engineering/alpha/agents/openai.yaml").unlink()
    (upstream.path / "skills/engineering/alpha/agents").rmdir()
    write_skill(upstream.path / "skills/engineering/alpha", "alpha", "# alpha v2\n")
    v2 = upstream.commit("v2.0.0", tag="v2.0.0")

    r = run_update(dotfiles, upstream)

    assert "Syncing 2 skills from v2.0.0" in r.out
    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text().endswith("# alpha v2\n")
    assert not (dotfiles.root / "skills/common/alpha/agents").exists()
    assert load_manifest(dotfiles.manifest).release.commit == v2


def test_skill_removed_upstream_aborts_before_writing(
    dotfiles: Dotfiles, upstream: Upstream
) -> None:
    run_update(dotfiles, upstream)
    dotfiles.commit_all()
    beta = upstream.path / "skills/productivity/beta"
    (beta / "SKILL.md").unlink()
    beta.rmdir()
    upstream.commit("drop beta", tag="v2.0.0")

    with pytest.raises(AutomationError, match="missing upstream: beta"):
        run_update(dotfiles, upstream)
    assert (dotfiles.root / "skills/common/beta/SKILL.md").exists()
    assert load_manifest(dotfiles.manifest).release.tag == "v1.0.0"


def test_dirty_vendored_dir_blocks(dotfiles: Dotfiles, upstream: Upstream) -> None:
    run_update(dotfiles, upstream)  # leaves skills/ untracked
    with pytest.raises(AutomationError, match="uncommitted changes"):
        run_update(dotfiles, upstream)


def test_apply_failing_twice_is_an_automation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(AutomationError, match="failed twice"):
        apply_dotfiles(tmp_path)
    assert len(calls) == 2


def test_parser_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
    assert build_parser().parse_args(["update"]).command == "update"
