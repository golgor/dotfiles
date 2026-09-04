"""End-to-end through `run_update()` with local repos as release sources."""

import io
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from automation import AutomationError
from automation.process import run
from automation.skills.cli import apply_dotfiles, build_parser, run_update
from automation.skills.manifest import Manifest, load_manifest
from tests.helpers import Dotfiles, Upstream, git, write_skill


@dataclass
class Result:
    out: str
    err: str
    applied: bool
    changed: bool


def do_update(
    dotfiles: Dotfiles,
    upstream: Upstream | dict[str, Upstream],
    target: str | None = None,
) -> Result:
    out, err, applied = io.StringIO(), io.StringIO(), []

    def source_for(manifest: Manifest) -> Upstream:
        if isinstance(upstream, dict):
            res = upstream.get(manifest.name)
            assert isinstance(res, Upstream), f"no upstream for manifest {manifest.name}"
            return res
        return upstream

    changed = run_update(
        dotfiles.root,
        target_name=target,
        source_for=source_for,
        apply=applied.append,
        out=out,
        err=err,
    )
    return Result(out.getvalue(), err.getvalue(), applied == [dotfiles.root], changed)


def test_first_import_syncs_and_records(dotfiles: Dotfiles, upstream: Upstream) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    r = do_update(dotfiles, upstream)

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
    assert r.changed
    assert r.err == ""


def test_second_run_is_a_noop(dotfiles: Dotfiles, upstream: Upstream) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    do_update(dotfiles, upstream)
    dotfiles.commit_all()

    r = do_update(dotfiles, upstream)
    assert "nothing to do" in r.out
    assert not r.applied
    assert not r.changed


def test_newly_selected_skill_syncs_at_current_release(
    dotfiles: Dotfiles, upstream: Upstream
) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    do_update(dotfiles, upstream)
    dotfiles.commit_all()
    release = load_manifest(dotfiles.manifest).release
    dotfiles.write_manifest(
        common=["alpha", "beta"], claude=["extra"], tag=release.tag, commit=release.commit
    )

    r = do_update(dotfiles, upstream)

    assert "Syncing 3 skills" in r.out
    assert (dotfiles.root / "skills/claude/extra/SKILL.md").exists()
    assert "extra is Claude-only but mise.toml has no entry" in r.err


def test_deselected_skill_is_reported_as_orphan(dotfiles: Dotfiles, upstream: Upstream) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    do_update(dotfiles, upstream)
    dotfiles.commit_all()
    release = load_manifest(dotfiles.manifest).release
    dotfiles.write_manifest(common=["alpha"], tag=release.tag, commit=release.commit)

    r = do_update(dotfiles, upstream)

    assert "nothing to do" in r.out
    assert "warning: skills/common/beta matches an upstream skill but is not selected" in r.err
    assert (dotfiles.root / "skills/common/beta").exists()  # never deleted silently


def test_local_edit_blocks_update(dotfiles: Dotfiles, upstream: Upstream) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    do_update(dotfiles, upstream)
    (dotfiles.root / "skills/common/alpha/SKILL.md").write_text("forked!\n")
    dotfiles.commit_all("local fork")
    upstream.commit("v1.1.0", tag="v1.1.0")

    with pytest.raises(AutomationError, match="differs from locked release: skills/common/alpha"):
        do_update(dotfiles, upstream)
    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text() == "forked!\n"


def test_release_bump_deletes_removed_files_and_records(
    dotfiles: Dotfiles, upstream: Upstream
) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    do_update(dotfiles, upstream)
    dotfiles.commit_all()
    (upstream.path / "skills/engineering/alpha/agents/openai.yaml").unlink()
    (upstream.path / "skills/engineering/alpha/agents").rmdir()
    write_skill(upstream.path / "skills/engineering/alpha", "alpha", "# alpha v2\n")
    v2 = upstream.commit("v2.0.0", tag="v2.0.0")

    r = do_update(dotfiles, upstream)

    assert "Syncing 2 skills from v2.0.0" in r.out
    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text().endswith("# alpha v2\n")
    assert not (dotfiles.root / "skills/common/alpha/agents").exists()
    assert load_manifest(dotfiles.manifest).release.commit == v2


def test_skill_removed_upstream_aborts_before_writing(
    dotfiles: Dotfiles, upstream: Upstream
) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    do_update(dotfiles, upstream)
    dotfiles.commit_all()
    beta = upstream.path / "skills/productivity/beta"
    (beta / "SKILL.md").unlink()
    beta.rmdir()
    upstream.commit("drop beta", tag="v2.0.0")

    with pytest.raises(AutomationError, match="missing upstream: beta"):
        do_update(dotfiles, upstream)
    assert (dotfiles.root / "skills/common/beta/SKILL.md").exists()
    assert load_manifest(dotfiles.manifest).release.tag == "v1.0.0"


def test_dirty_vendored_dir_blocks(dotfiles: Dotfiles, upstream: Upstream) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    do_update(dotfiles, upstream)  # leaves skills/ untracked
    with pytest.raises(AutomationError, match="uncommitted changes"):
        do_update(dotfiles, upstream)


def test_multi_manifest_updates_all_and_applies_once(
    dotfiles: Dotfiles, upstream: Upstream, tmp_path: Path
) -> None:
    dotfiles.manifest.unlink()
    dotfiles.write_manifest("first", common=["alpha"])
    up2_path = tmp_path / "up2"
    up2_path.mkdir()
    git("init", "-q", cwd=up2_path)
    write_skill(up2_path / "plugins/docs/skills/gamma", "gamma", "# gamma v1\n")
    up2 = Upstream(up2_path, branch="main")
    up2.commit("init", branch="main")
    dotfiles.write_manifest("second", repo="work/other", branch="main", common=["gamma"])

    r = do_update(dotfiles, {"first": upstream, "second": up2})

    assert (dotfiles.root / "skills/common/alpha/SKILL.md").exists()
    assert (dotfiles.root / "skills/common/gamma/SKILL.md").exists()
    assert r.applied
    assert "[first]" in r.out
    assert "[second]" in r.out


def test_single_manifest_targeted_update(
    dotfiles: Dotfiles, upstream: Upstream, tmp_path: Path
) -> None:
    dotfiles.manifest.unlink()
    dotfiles.write_manifest("first", common=["alpha"])
    up2_path = tmp_path / "up2"
    up2_path.mkdir()
    git("init", "-q", cwd=up2_path)
    write_skill(up2_path / "gamma", "gamma")
    up2 = Upstream(up2_path, branch="main")
    up2.commit("init", branch="main")
    dotfiles.write_manifest("second", repo="work/other", branch="main", common=["gamma"])

    r = do_update(dotfiles, {"first": upstream, "second": up2}, target="first")

    assert (dotfiles.root / "skills/common/alpha/SKILL.md").exists()
    assert not (dotfiles.root / "skills/common/gamma/SKILL.md").exists()
    assert r.applied


def test_missing_target_manifest_reports_available(dotfiles: Dotfiles, upstream: Upstream) -> None:
    dotfiles.manifest.unlink()
    dotfiles.write_manifest("first", common=["alpha"])
    with pytest.raises(
        AutomationError, match=r"manifest 'nonexistent' not found\. Available: first"
    ):
        do_update(dotfiles, upstream, target="nonexistent")


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


def test_missing_executable_is_an_automation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))  # nothing on PATH
    with pytest.raises(AutomationError, match="cannot run `mise`"):
        apply_dotfiles(tmp_path)
    with pytest.raises(AutomationError, match="cannot run `definitely-not-a-command`"):
        run("definitely-not-a-command")


def test_parser_accepts_optional_manifest_argument() -> None:
    assert build_parser().parse_args(["update"]).manifest is None
    assert build_parser().parse_args(["update", "mattpocock"]).manifest == "mattpocock"
