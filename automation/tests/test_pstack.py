"""Acceptance tests for the adopted pstack bundle and its deployment contract."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills.deploy import HARNESSES, deploy_skills

REPO_ROOT = Path(__file__).resolve().parents[2]
PSTACK = REPO_ROOT / "skills/pstack"

# Inventory from pstack commit 9b93e81fb2921b9263d9463c15bafeabfe3903aa.
PRIMARY_SKILLS = frozenset(
    {
        "architect",
        "arena",
        "automate-me",
        "benchmark-checklist",
        "blast-radius",
        "bro",
        "correct",
        "create-formal-verification-skill",
        "create-verification-skill",
        "figure-it-out",
        "how",
        "interrogate",
        "in-your-own-words",
        "ketchup",
        "maintain-formal-verification-skill",
        "maintain-verification-skill",
        "make-bot-ui",
        "no-comments",
        "poteto-help",
        "poteto-mode",
        "principle-attack-the-premise",
        "principle-boundary-discipline",
        "principle-build-the-lever",
        "principle-encode-lessons-in-structure",
        "principle-exhaust-the-design-space",
        "principle-experience-first",
        "principle-explain-the-number",
        "principle-fix-root-causes",
        "principle-foundational-thinking",
        "principle-guard-the-context-window",
        "principle-laziness-protocol",
        "principle-make-operations-idempotent",
        "principle-migrate-callers-then-delete-legacy-apis",
        "principle-minimize-reader-load",
        "principle-model-the-domain",
        "principle-never-block-on-the-human",
        "principle-outcome-oriented-execution",
        "principle-prove-it-works",
        "principle-redesign-from-first-principles",
        "principle-separate-before-serializing-shared-state",
        "principle-sequence-verifiable-units",
        "principle-subtract-before-you-add",
        "principle-test-behavior-not-implementation",
        "principle-type-system-discipline",
        "recall",
        "reflect",
        "setup-pstack",
        "sharpen",
        "show-me-your-work",
        "statechart",
        "swarm",
        "tdd",
        "teach",
        "technical-writing",
        "typescript-best-practices",
        "unslop",
        "why",
    }
)
ADOPTED_COMMIT = "9b93e81fb2921b9263d9463c15bafeabfe3903aa"


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    assert match, "SKILL.md must start with YAML frontmatter"
    fields: dict[str, str] = {}
    for field_match in re.finditer(r"^([\w-]+):\s*(.+)$", match.group(1), re.MULTILINE):
        name, value = field_match.groups()
        assert isinstance(name, str) and isinstance(value, str)
        fields[name] = value
    body = match.group(2)
    assert isinstance(body, str)
    return fields, body


def test_pstack_has_verified_primary_inventory_and_skill_conventions() -> None:
    names = {path.name for path in PSTACK.iterdir() if path.is_dir()}
    assert len(PRIMARY_SKILLS) == 57
    assert names == PRIMARY_SKILLS

    for name in sorted(PRIMARY_SKILLS):
        skill = PSTACK / name
        fields, body = _frontmatter((skill / "SKILL.md").read_text())
        assert fields["name"] == name
        assert fields.get("description", "").strip()
        assert "PSTACK-HARNESS.md" in body

        source = (skill / "SOURCE.md").read_text()
        assert "Upstream repository: `https://github.com/cursor/plugins`" in source
        plugin_root = (
            "Plugin root: `https://github.com/cursor/plugins/tree/"
            "9b93e81fb2921b9263d9463c15bafeabfe3903aa/pstack`"
        )
        assert plugin_root in source
        assert f"Source path: `pstack/skills/{name}/`" in source
        skill_origin = (
            "Skill origin: `https://github.com/cursor/plugins/tree/"
            f"9b93e81fb2921b9263d9463c15bafeabfe3903aa/pstack/skills/{name}`"
        )
        assert skill_origin in source
        assert "/plugins/" + "pstack" not in source
        assert ADOPTED_COMMIT in source
        assert "License:" in source
        assert (skill / "LICENSE").is_file()
        assert "MIT License" in (skill / "LICENSE").read_text()


def test_pstack_bridge_and_profiles_are_files_with_expected_public_shapes() -> None:
    bridge = PSTACK / "PSTACK-HARNESS.md"
    assert bridge.is_file() and not bridge.is_dir()

    profile = REPO_ROOT / ".pi/agent/agents/poteto-agent.md"
    fields, body = _frontmatter(profile.read_text())
    assert fields["name"] == "poteto-agent"
    assert fields.get("description", "").strip()
    assert body.strip()

    reader = REPO_ROOT / ".pi/agent/agents/pstack-reader.md"
    reader_fields, reader_body = _frontmatter(reader.read_text())
    assert reader_fields["name"] == "pstack-reader"
    assert reader_fields["tools"] == "read, bash"
    assert reader_fields["inheritProjectContext"] == "true"
    assert reader_fields["inheritGlobalContext"] == "true"
    assert reader_fields["inheritSkills"] == "true"
    assert "model:" not in reader_fields
    assert "Do not edit files" in reader_body

    # The adopted pstack agent keeps the existing comment-sicko body intact.
    comment_sicko = REPO_ROOT / ".pi/agent/agents/comment-sicko.md"
    body_hash = hashlib.sha256(_frontmatter(comment_sicko.read_text())[1].encode()).hexdigest()
    assert body_hash == "334fc4d4eabf6b22c0a0c68203b259e9d6212506f8d7b720b300da2b0abcff21"


def test_pstack_selection_projects_stack_and_common_to_all_harnesses(tmp_path: Path) -> None:
    home = tmp_path / "home"
    deploy_skills(REPO_ROOT, home, stack="pstack")

    common = [path.name for path in (REPO_ROOT / "skills/common").iterdir() if path.is_dir()]
    assert not PRIMARY_SKILLS.intersection(common)
    for harness in HARNESSES:
        discovery = home / harness.directory
        for name in (*PRIMARY_SKILLS, *common):
            link = discovery / name
            expected_scope = "common" if name in common else "pstack"
            assert link.is_symlink()
            assert link.resolve() == (REPO_ROOT / "skills" / expected_scope / name).resolve()
            assert link.is_dir()

    claude_names = {path.name for path in (REPO_ROOT / "skills/claude").iterdir() if path.is_dir()}
    assert claude_names
    for name in claude_names:
        assert (home / ".claude/skills" / name).is_symlink()
        assert not (home / ".agents/skills" / name).exists()
        assert not (home / ".codex/skills" / name).exists()


def test_switching_stack_prunes_managed_links_and_preserves_foreign_neighbours(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    deploy_skills(REPO_ROOT, home, stack="pstack")
    for harness in HARNESSES:
        neighbour = home / harness.directory / "foreign-neighbour"
        neighbour.mkdir()
        (neighbour / "keep.txt").write_text("keep")

    deploy_skills(REPO_ROOT, home, stack="matt")
    matt_names = {path.name for path in (REPO_ROOT / "skills/matt").iterdir() if path.is_dir()}
    for harness in HARNESSES:
        discovery = home / harness.directory
        assert (discovery / "foreign-neighbour" / "keep.txt").read_text() == "keep"
        for name in PRIMARY_SKILLS - matt_names:
            assert not (discovery / name).exists()


def test_foreign_collision_blocks_pstack_deployment_without_clobbering(tmp_path: Path) -> None:
    home = tmp_path / "home"
    deploy_skills(REPO_ROOT, home, stack="matt")
    blocker = home / ".codex/skills/tdd"
    blocker.unlink()
    blocker.mkdir()
    (blocker / "keep.txt").write_text("keep")

    with pytest.raises(AutomationError, match=str(blocker)):
        deploy_skills(REPO_ROOT, home, stack="pstack")
    assert (blocker / "keep.txt").read_text() == "keep"
