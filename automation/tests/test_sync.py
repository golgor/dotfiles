from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills import sync
from automation.skills.manifest import load_manifest
from tests.helpers import Dotfiles, write_skill


def test_require_clean_ignores_manifest_but_not_vendored_dirs(dotfiles: Dotfiles) -> None:
    dotfiles.manifest.write_text(dotfiles.manifest.read_text() + "# edited\n")
    sync.require_clean(dotfiles.root)  # manifest edits are the normal workflow

    write_skill(dotfiles.root / "skills/common/alpha", "alpha")
    with pytest.raises(AutomationError, match="uncommitted changes"):
        sync.require_clean(dotfiles.root)


def test_trees_differ(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    write_skill(a / "s", "s", "same")
    write_skill(b / "s", "s", "same")
    assert not sync.trees_differ(a, b)

    (b / "s/extra.md").write_text("x")
    assert sync.trees_differ(a, b)  # right_only
    (b / "s/extra.md").unlink()

    (b / "s/SKILL.md").write_text((b / "s/SKILL.md").read_text() + "!")
    assert sync.trees_differ(a, b)  # content, same size class -> needs shallow=False


def test_check_against_locked_passes_when_identical_or_absent(
    dotfiles: Dotfiles, tmp_path: Path
) -> None:
    write_skill(dotfiles.root / "skills/common/alpha", "alpha", "v1")
    write_skill(tmp_path / "locked/alpha", "alpha", "v1")
    manifest = load_manifest(dotfiles.manifest)  # alpha, beta selected; beta absent locally

    sync.check_against_locked(dotfiles.root, manifest, {"alpha": tmp_path / "locked/alpha"})


def test_check_against_locked_reports_divergent_and_unmanaged(
    dotfiles: Dotfiles, tmp_path: Path
) -> None:
    write_skill(dotfiles.root / "skills/common/alpha", "alpha", "edited locally")
    write_skill(dotfiles.root / "skills/common/beta", "beta", "not in locked release")
    write_skill(tmp_path / "locked/alpha", "alpha", "v1")
    manifest = load_manifest(dotfiles.manifest)

    with pytest.raises(AutomationError) as exc:
        sync.check_against_locked(dotfiles.root, manifest, {"alpha": tmp_path / "locked/alpha"})
    message = str(exc.value)
    assert "differs from locked release: skills/common/alpha" in message
    assert "exists locally but not in locked release: skills/common/beta" in message
    assert "refusing to overwrite" in message


def test_sync_skill_copies_verbatim_and_deletes_removed(tmp_path: Path) -> None:
    src, dest = tmp_path / "src", tmp_path / "dest"
    write_skill(src, "s")
    (src / "scripts").mkdir()
    (src / "scripts/run.sh").write_text("#!/bin/sh\n")
    (src / "scripts/run.sh").chmod(0o755)
    write_skill(dest, "s", "old")
    (dest / "stale.md").write_text("gone upstream")

    sync.sync_skill(src, dest)

    assert (dest / "SKILL.md").read_text() == (src / "SKILL.md").read_text()
    assert not (dest / "stale.md").exists()
    assert (dest / "scripts/run.sh").stat().st_mode & 0o111


def test_orphans_and_all_present(dotfiles: Dotfiles) -> None:
    manifest = load_manifest(dotfiles.manifest)  # alpha, beta
    assert not sync.all_present(dotfiles.root, manifest)

    write_skill(dotfiles.root / "skills/common/alpha", "alpha")
    write_skill(dotfiles.root / "skills/common/beta", "beta")
    write_skill(dotfiles.root / "skills/common/extra", "extra")  # upstream name, not selected
    write_skill(dotfiles.root / "skills/common/mine", "mine")  # not upstream at all

    assert sync.all_present(dotfiles.root, manifest)
    assert sync.orphans(dotfiles.root, manifest, {"alpha", "beta", "extra"}) == [
        Path("skills/common/extra")
    ]


def test_orphans_flags_stale_copy_after_scope_move(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"], claude=["beta"])  # beta moved common -> claude
    manifest = load_manifest(dotfiles.manifest)
    write_skill(dotfiles.root / "skills/common/beta", "beta")  # old location
    write_skill(dotfiles.root / "skills/claude/beta", "beta")  # new location

    assert sync.orphans(dotfiles.root, manifest, {"alpha", "beta"}) == [Path("skills/common/beta")]


def test_missing_claude_entries(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"], claude=["beta", "gamma"])
    manifest = load_manifest(dotfiles.manifest)
    mise_toml = '"~/.claude/skills/beta" = { source = "skills/claude/beta", mode = "symlink" }\n'
    assert sync.missing_claude_entries(mise_toml, manifest) == ["gamma"]
