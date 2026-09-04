"""End-to-end through `update()` with a local tagged repo as the release source."""

import io
from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills.cli import build_parser, update
from automation.skills.manifest import load_manifest
from tests.conftest import Dotfiles, Upstream, write_skill


def run_update(dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]) -> tuple[str, str]:
    out, err = io.StringIO(), io.StringIO()
    update(dotfiles.root, lambda _repo: upstream, applied.append, out, err)
    return out.getvalue(), err.getvalue()


def test_first_import_syncs_and_records(
    dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]
) -> None:
    out, err = run_update(dotfiles, upstream, applied)

    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text().endswith("# alpha v1\n")
    assert (dotfiles.root / "skills/common/alpha/agents/openai.yaml").exists()
    assert (dotfiles.root / "skills/common/beta/SKILL.md").exists()
    assert not (dotfiles.root / "skills/common/extra").exists()

    release = load_manifest(dotfiles.manifest).release
    assert release.tag == "v1.0.0" and len(release.commit) == 40
    assert "# header comment survives" in dotfiles.manifest.read_text()

    assert "No locked release yet" in out
    assert "Syncing 2 skills from v1.0.0" in out
    assert "not selected (1):\n  extra" in out
    assert applied == [dotfiles.root]
    assert err == ""


def test_second_run_is_a_noop(dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]) -> None:
    run_update(dotfiles, upstream, applied)
    dotfiles.commit_all()

    out, _ = run_update(dotfiles, upstream, applied)
    assert "nothing to do" in out
    assert applied == [dotfiles.root]  # not applied again


def test_newly_selected_skill_syncs_at_current_release(
    dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]
) -> None:
    run_update(dotfiles, upstream, applied)
    dotfiles.commit_all()
    release = load_manifest(dotfiles.manifest).release
    dotfiles.write_manifest(
        common=["alpha", "beta"], claude=["extra"], tag=release.tag, commit=release.commit
    )

    out, err = run_update(dotfiles, upstream, applied)

    assert "Syncing 3 skills" in out
    assert (dotfiles.root / "skills/claude/extra/SKILL.md").exists()
    assert "extra is Claude-only but mise.toml has no entry" in err


def test_deselected_skill_is_reported_as_orphan(
    dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]
) -> None:
    run_update(dotfiles, upstream, applied)
    dotfiles.commit_all()
    release = load_manifest(dotfiles.manifest).release
    dotfiles.write_manifest(common=["alpha"], tag=release.tag, commit=release.commit)

    out, err = run_update(dotfiles, upstream, applied)

    assert "nothing to do" in out
    assert "warning: skills/common/beta matches an upstream skill but is not selected" in err
    assert (dotfiles.root / "skills/common/beta").exists()  # never deleted silently


def test_local_edit_blocks_update(
    dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]
) -> None:
    run_update(dotfiles, upstream, applied)
    (dotfiles.root / "skills/common/alpha/SKILL.md").write_text("forked!\n")
    dotfiles.commit_all("local fork")
    upstream.commit("v1.1.0", tag="v1.1.0")

    with pytest.raises(AutomationError, match="differs from locked release: skills/common/alpha"):
        run_update(dotfiles, upstream, applied)
    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text() == "forked!\n"


def test_release_bump_deletes_removed_files_and_records(
    dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]
) -> None:
    run_update(dotfiles, upstream, applied)
    dotfiles.commit_all()
    (upstream.path / "skills/engineering/alpha/agents/openai.yaml").unlink()
    (upstream.path / "skills/engineering/alpha/agents").rmdir()
    write_skill(upstream.path / "skills/engineering/alpha", "alpha", "# alpha v2\n")
    v2 = upstream.commit("v2.0.0", tag="v2.0.0")

    out, _ = run_update(dotfiles, upstream, applied)

    assert "Syncing 2 skills from v2.0.0" in out
    assert (dotfiles.root / "skills/common/alpha/SKILL.md").read_text().endswith("# alpha v2\n")
    assert not (dotfiles.root / "skills/common/alpha/agents").exists()
    assert load_manifest(dotfiles.manifest).release.commit == v2


def test_skill_removed_upstream_aborts_before_writing(
    dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]
) -> None:
    run_update(dotfiles, upstream, applied)
    dotfiles.commit_all()
    beta = upstream.path / "skills/productivity/beta"
    (beta / "SKILL.md").unlink()
    beta.rmdir()
    upstream.commit("drop beta", tag="v2.0.0")

    with pytest.raises(AutomationError, match="missing upstream: beta"):
        run_update(dotfiles, upstream, applied)
    assert (dotfiles.root / "skills/common/beta/SKILL.md").exists()
    assert load_manifest(dotfiles.manifest).release.tag == "v1.0.0"


def test_dirty_vendored_dir_blocks(
    dotfiles: Dotfiles, upstream: Upstream, applied: list[Path]
) -> None:
    run_update(dotfiles, upstream, applied)  # leaves skills/ untracked
    with pytest.raises(AutomationError, match="uncommitted changes"):
        run_update(dotfiles, upstream, applied)


def test_parser_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
    assert build_parser().parse_args(["update"]).command == "update"
