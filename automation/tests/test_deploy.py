"""`deploy_skills`: project directory symlinks into every harness discovery directory."""

import os
import shutil
from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills import deploy
from automation.skills.deploy import HARNESSES
from tests.helpers import write_skill


def make_root(tmp_path: Path) -> Path:
    root = tmp_path / "dotfiles"
    root.mkdir()
    return root


def test_deploy_links_every_scope_into_every_harness(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")
    write_skill(root / "skills/claude/handoff", "handoff")

    result = deploy.deploy_skills(root, home)

    pi_link = home / ".agents/skills/alpha"
    codex_link = home / ".codex/skills/alpha"
    claude_common_link = home / ".claude/skills/alpha"
    claude_only_link = home / ".claude/skills/handoff"

    assert pi_link.resolve() == (root / "skills/common/alpha").resolve()
    assert codex_link.resolve() == (root / "skills/common/alpha").resolve()
    assert claude_common_link.resolve() == (root / "skills/common/alpha").resolve()
    assert claude_only_link.resolve() == (root / "skills/claude/handoff").resolve()

    # Claude-only skill must not leak into Pi or Codex.
    assert not (home / ".agents/skills/handoff").exists()
    assert not (home / ".codex/skills/handoff").exists()

    assert set(result.linked) == {pi_link, codex_link, claude_common_link, claude_only_link}
    assert result.pruned == []
    assert result.unchanged == []


def test_created_link_is_a_directory_symlink_readable_through(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha", "# alpha body\n")

    deploy.deploy_skills(root, home)

    link = home / ".agents/skills/alpha"
    assert link.is_symlink()
    assert link.is_dir()
    expected = "---\nname: alpha\ndescription: Does things.\n---\n# alpha body\n"
    assert (link / "SKILL.md").read_text() == expected


def test_second_run_is_idempotent(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")
    write_skill(root / "skills/claude/handoff", "handoff")

    deploy.deploy_skills(root, home)
    result = deploy.deploy_skills(root, home)

    assert result.linked == []
    assert result.pruned == []
    assert len(result.unchanged) == 4  # alpha x3 harnesses + handoff x1


def test_neighbours_are_preserved_untouched(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    outside_target = tmp_path / "elsewhere"
    outside_target.mkdir()

    for harness in HARNESSES:
        discovery = home / harness.directory
        discovery.mkdir(parents=True, exist_ok=True)
        (discovery / "hey").mkdir()  # real, harness-owned directory
        (discovery / "hey" / "SKILL.md").write_text("owned by hey")
        (discovery / "omarchy").symlink_to(outside_target, target_is_directory=True)

    (home / ".codex/skills/.system").mkdir(parents=True)
    (home / ".codex/skills/.system/README.md").write_text("codex system skills")
    (home / ".claude/skills/synced").mkdir(parents=True)
    (home / ".claude/skills/synced/README.md").write_text("claude.ai synced skills")

    result = deploy.deploy_skills(root, home)

    for harness in HARNESSES:
        discovery = home / harness.directory
        hey = discovery / "hey"
        omarchy = discovery / "omarchy"
        assert hey.is_dir() and not hey.is_symlink()
        assert (hey / "SKILL.md").read_text() == "owned by hey"
        assert omarchy.is_symlink()
        assert omarchy.resolve() == outside_target.resolve()

    assert (home / ".codex/skills/.system/README.md").read_text() == "codex system skills"
    assert (home / ".claude/skills/synced/README.md").read_text() == "claude.ai synced skills"

    touched = set(result.linked) | set(result.pruned) | set(result.unchanged)
    for harness in HARNESSES:
        discovery = home / harness.directory
        assert discovery / "hey" not in touched
        assert discovery / "omarchy" not in touched
    assert (home / ".codex/skills/.system") not in touched
    assert (home / ".claude/skills/synced") not in touched


def test_removing_a_skill_prunes_its_links_including_dangling(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    deploy.deploy_skills(root, home)

    shutil.rmtree(root / "skills/common/alpha")

    result = deploy.deploy_skills(root, home)

    pi_link = home / ".agents/skills/alpha"
    codex_link = home / ".codex/skills/alpha"
    claude_link = home / ".claude/skills/alpha"

    assert not pi_link.exists() and not pi_link.is_symlink()
    assert not codex_link.exists() and not codex_link.is_symlink()
    assert not claude_link.exists() and not claude_link.is_symlink()
    assert set(result.pruned) == {pi_link, codex_link, claude_link}
    assert result.linked == []


def test_repoints_managed_link_when_skill_moves_scope(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/beta", "beta")

    deploy.deploy_skills(root, home)

    shutil.move(str(root / "skills/common/beta"), str(root / "skills/claude/beta"))

    result = deploy.deploy_skills(root, home)

    claude_link = home / ".claude/skills/beta"
    assert claude_link.resolve() == (root / "skills/claude/beta").resolve()
    assert claude_link in result.linked

    # No longer reachable from Pi or Codex (common scope only reaches those two).
    assert not (home / ".agents/skills/beta").exists()
    assert not (home / ".codex/skills/beta").exists()


def test_conflict_real_directory_raises_and_does_not_clobber(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    blocker = home / ".agents/skills/alpha"
    blocker.mkdir(parents=True)
    (blocker / "keepme.txt").write_text("do not clobber")

    with pytest.raises(AutomationError, match=str(blocker)):
        deploy.deploy_skills(root, home)

    assert (blocker / "keepme.txt").read_text() == "do not clobber"
    assert not blocker.is_symlink()


def test_conflict_real_file_raises_and_does_not_clobber(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    blocker = home / ".agents/skills/alpha"
    blocker.parent.mkdir(parents=True)
    blocker.write_text("not a skill directory")

    with pytest.raises(AutomationError, match=str(blocker)):
        deploy.deploy_skills(root, home)

    assert blocker.is_file()
    assert blocker.read_text() == "not a skill directory"


def test_conflict_symlink_pointing_outside_skills_raises(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    outside_target = tmp_path / "elsewhere"
    outside_target.mkdir()
    blocker = home / ".agents/skills/alpha"
    blocker.parent.mkdir(parents=True)
    blocker.symlink_to(outside_target, target_is_directory=True)

    with pytest.raises(AutomationError, match=str(blocker)):
        deploy.deploy_skills(root, home)

    assert blocker.is_symlink()
    assert blocker.resolve() == outside_target.resolve()


def test_conflicts_across_harnesses_are_all_reported_together(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    pi_blocker = home / ".agents/skills/alpha"
    codex_blocker = home / ".codex/skills/alpha"
    pi_blocker.mkdir(parents=True)
    codex_blocker.mkdir(parents=True)

    with pytest.raises(AutomationError) as exc:
        deploy.deploy_skills(root, home)
    message = str(exc.value)
    assert str(pi_blocker) in message
    assert str(codex_blocker) in message


def test_missing_harness_directory_is_created_missing_scope_dir_is_not_an_error(
    tmp_path: Path,
) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")
    # skills/claude does not exist at all.

    result = deploy.deploy_skills(root, home)

    assert (home / ".claude/skills").is_dir()
    assert (home / ".agents/skills/alpha").is_symlink()
    assert result.linked  # no error raised for the absent claude scope directory


def test_harnesses_table_shape() -> None:
    names = {h.name for h in HARNESSES}
    assert names == {"Pi", "Claude Code", "Codex"}
    by_name = {h.name: h for h in HARNESSES}
    assert by_name["Pi"].scopes == ("common",)
    assert by_name["Codex"].scopes == ("common",)
    assert by_name["Claude Code"].scopes == ("common", "claude")


# -- _classify: what is at a path, and whether it is ours to touch --


def test_classify_free_when_nothing_at_path(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills").mkdir(parents=True)
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)

    skills_root = (root / "skills").resolve()
    assert deploy._classify(link_dir / "absent", skills_root) is deploy._Occupancy.FREE


def test_classify_managed_for_ordinary_absolute_link_into_skills_root(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    link = link_dir / "alpha"
    link.symlink_to(root / "skills/common/alpha", target_is_directory=True)

    skills_root = (root / "skills").resolve()
    assert deploy._classify(link, skills_root) is deploy._Occupancy.MANAGED


def test_classify_managed_for_relative_target_into_skills_root(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/tdd", "tdd")
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    link = link_dir / "tdd"
    relative_target = Path(os.path.relpath(root / "skills/common/tdd", link_dir))
    link.symlink_to(relative_target, target_is_directory=True)

    skills_root = (root / "skills").resolve()
    assert deploy._classify(link, skills_root) is deploy._Occupancy.MANAGED


def test_classify_managed_for_dangling_link_into_skills_root(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills").mkdir(parents=True)
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    link = link_dir / "gone"
    # Target never existed (or was since removed); pruning depends on this still
    # classifying as ours.
    link.symlink_to(root / "skills/common/gone", target_is_directory=True)

    skills_root = (root / "skills").resolve()
    assert deploy._classify(link, skills_root) is deploy._Occupancy.MANAGED


def test_classify_rejects_target_that_escapes_skills_root_via_dotdot(
    tmp_path: Path,
) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills").mkdir(parents=True)
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    link = link_dir / "escaped"
    # Lexically starts with root/skills, but the trailing `../..` walks back out to a
    # sibling of root entirely. A naive is_relative_to() on the un-normalised path
    # would wrongly call this managed.
    escaping_target = root / "skills" / ".." / ".." / "important"
    link.symlink_to(escaping_target, target_is_directory=True)

    skills_root = (root / "skills").resolve()
    assert deploy._classify(link, skills_root) is deploy._Occupancy.FOREIGN


def test_classify_rejects_sibling_skills_backup_directory(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills-backup").mkdir(parents=True)
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    link = link_dir / "sneaky"
    link.symlink_to(root / "skills-backup" / "x", target_is_directory=True)

    skills_root = (root / "skills").resolve()
    assert deploy._classify(link, skills_root) is deploy._Occupancy.FOREIGN


def test_classify_foreign_for_link_to_somewhere_unrelated(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills").mkdir(parents=True)
    outside_target = tmp_path / "elsewhere"
    outside_target.mkdir()
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    link = link_dir / "omarchy"
    link.symlink_to(outside_target, target_is_directory=True)

    skills_root = (root / "skills").resolve()
    assert deploy._classify(link, skills_root) is deploy._Occupancy.FOREIGN


def test_classify_foreign_for_real_file(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills").mkdir(parents=True)
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    path = link_dir / "blocker"
    path.write_text("not a skill directory")

    skills_root = (root / "skills").resolve()
    assert deploy._classify(path, skills_root) is deploy._Occupancy.FOREIGN


def test_classify_foreign_for_real_directory(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills").mkdir(parents=True)
    link_dir = home / ".agents/skills"
    link_dir.mkdir(parents=True)
    path = link_dir / "hey"
    path.mkdir()

    skills_root = (root / "skills").resolve()
    assert deploy._classify(path, skills_root) is deploy._Occupancy.FOREIGN


def test_classify_foreign_for_dangling_link_with_target_outside_skills_root(
    tmp_path: Path,
) -> None:
    """The regression case: a dangling symlink's occupancy depends on its target, not
    on exists(). A naive exists()-based check treats every dangling symlink the same
    as an absent path (FREE); classifying by target instead means a dangling discovery
    path pointed outside skills_root is correctly FOREIGN, not FREE.
    """
    root, home = make_root(tmp_path), tmp_path / "home"
    (root / "skills").mkdir(parents=True)
    link_dir = home / ".agents"
    link_dir.mkdir(parents=True)
    discovery = link_dir / "skills"
    discovery.symlink_to(tmp_path / "does-not-exist")

    skills_root = (root / "skills").resolve()
    assert deploy._classify(discovery, skills_root) is deploy._Occupancy.FOREIGN


# -- atomicity: plan across every harness before writing anything --


def test_conflict_in_one_harness_prevents_writes_everywhere(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")
    deploy.deploy_skills(root, home)  # baseline: every harness fully linked

    # A new skill to link, and an old one to prune, in the same run.
    write_skill(root / "skills/common/gamma", "gamma")
    shutil.rmtree(root / "skills/common/alpha")

    # Conflict: Pi's desired gamma link is blocked by a real directory.
    pi_gamma = home / ".agents/skills/gamma"
    pi_gamma.mkdir(parents=True)

    codex_alpha = home / ".codex/skills/alpha"
    claude_alpha = home / ".claude/skills/alpha"

    with pytest.raises(AutomationError, match=str(pi_gamma)):
        deploy.deploy_skills(root, home)

    # Nothing pruned: alpha's stale links, due for removal in this same run, survive
    # in the harnesses that never conflicted.
    assert codex_alpha.is_symlink()
    assert claude_alpha.is_symlink()
    # Nothing created: the new gamma skill was not linked anywhere, including the
    # harnesses that had no conflict of their own.
    assert not (home / ".codex/skills/gamma").exists()
    assert not (home / ".claude/skills/gamma").exists()
    # The conflicting path itself is untouched too.
    assert pi_gamma.is_dir() and not pi_gamma.is_symlink()


# -- duplicate destination name across scopes visible to one harness --


def test_duplicate_skill_name_across_scopes_raises(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    common_foo = root / "skills/common/foo"
    claude_foo = root / "skills/claude/foo"
    write_skill(common_foo, "foo")
    write_skill(claude_foo, "foo")

    with pytest.raises(AutomationError) as exc:
        deploy.deploy_skills(root, home)
    message = str(exc.value)
    assert "foo" in message
    assert str(common_foo) in message
    assert str(claude_foo) in message


# -- discovery path is not a directory --


def test_discovery_path_that_is_a_file_raises_automation_error(tmp_path: Path) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    blocker = home / ".agents/skills"
    blocker.parent.mkdir(parents=True)
    blocker.write_text("not a directory")

    with pytest.raises(AutomationError, match=str(blocker)):
        deploy.deploy_skills(root, home)


def test_discovery_path_that_is_a_dangling_symlink_raises_and_does_not_clobber(
    tmp_path: Path,
) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    blocker = home / ".agents/skills"
    blocker.parent.mkdir(parents=True)
    blocker.symlink_to(tmp_path / "does-not-exist")

    with pytest.raises(AutomationError, match=str(blocker)):
        deploy.deploy_skills(root, home)

    assert blocker.is_symlink()
    assert not blocker.exists()
    # Atomic across harnesses: nothing was deployed anywhere else either.
    assert not (home / ".claude/skills").exists()
    assert not (home / ".codex/skills").exists()


def test_discovery_path_that_is_a_symlink_to_a_real_directory_is_accepted(
    tmp_path: Path,
) -> None:
    root, home = make_root(tmp_path), tmp_path / "home"
    write_skill(root / "skills/common/alpha", "alpha")

    real_dir = tmp_path / "real-agents-skills"
    real_dir.mkdir()
    discovery = home / ".agents/skills"
    discovery.parent.mkdir(parents=True)
    discovery.symlink_to(real_dir, target_is_directory=True)

    result = deploy.deploy_skills(root, home)

    link = discovery / "alpha"
    assert link.is_symlink()
    assert link.resolve() == (root / "skills/common/alpha").resolve()
    assert link in result.linked
    # The link was actually created inside the symlink's target directory.
    assert (real_dir / "alpha").is_symlink()
