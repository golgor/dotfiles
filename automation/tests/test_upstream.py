from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills import upstream as up
from tests.conftest import Upstream, git, write_skill


def test_discover_finds_skills_recursively_by_name(upstream: Upstream) -> None:
    found = up.discover_skills(upstream.path)
    assert set(found) == {"alpha", "beta", "extra"}
    assert found["alpha"] == [upstream.path / "skills/engineering/alpha"]


def test_discover_skips_git_dir(tmp_path: Path) -> None:
    write_skill(tmp_path / ".git/hooks/sneaky", "sneaky")
    write_skill(tmp_path / "real", "real")
    assert set(up.discover_skills(tmp_path)) == {"real"}


def test_resolve_selected_reports_missing_and_ambiguous(tmp_path: Path) -> None:
    write_skill(tmp_path / "a/dup", "dup")
    write_skill(tmp_path / "b/dup", "dup")
    write_skill(tmp_path / "ok", "ok")
    found = up.discover_skills(tmp_path)

    with pytest.raises(AutomationError) as exc:
        up.resolve_selected(found, ["ok", "dup", "gone"])
    message = str(exc.value)
    assert "missing upstream: gone" in message
    assert "ambiguous upstream: dup" in message
    assert "nothing was changed" in message

    assert up.resolve_selected(found, ["ok"]) == {"ok": tmp_path / "ok"}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("---\nname: x\ndescription: Plain.\n---\n", {"name": "x", "description": "Plain."}),
        (
            "---\nname: 'x'\ndescription: \"Quoted.\"\n---\n",
            {"name": "x", "description": "Quoted."},
        ),
        (
            "---\nname: x\ndescription: >-\n  Folded block\n  more\n---\n",
            {"name": "x", "description": "Folded block"},
        ),
        ("---\nname: x\ndescription: |\n---\n", {"name": "x", "description": ""}),
        ("no frontmatter\n", {}),
        ("---\nname: x\n", {"name": "x"}),
    ],
)
def test_frontmatter_fields(tmp_path: Path, text: str, expected: dict[str, str]) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(text)
    assert up.frontmatter_fields(skill_md) == expected


def test_validate_skill_passes_well_formed(tmp_path: Path) -> None:
    write_skill(tmp_path / "good", "good")
    assert up.validate_skill("good", tmp_path / "good") == []


def test_validate_skill_collects_every_problem(tmp_path: Path) -> None:
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "SKILL.md").write_text("---\nname: other\n---\n")
    (bad / "nested").mkdir()
    (bad / "nested/SKILL.md").write_text("---\nname: nested\ndescription: d\n---\n")

    assert up.validate_skill("bad", bad) == [
        "expected exactly one SKILL.md",
        "frontmatter name 'other' != directory 'bad'",
        "frontmatter has no description",
    ]


def test_validate_all_raises_with_names(tmp_path: Path) -> None:
    write_skill(tmp_path / "good", "good")
    (tmp_path / "bad").mkdir()
    (tmp_path / "bad/SKILL.md").write_text("nope\n")
    with pytest.raises(AutomationError, match=r"integrity checks.*\n  bad: "):
        up.validate_all({"good": tmp_path / "good", "bad": tmp_path / "bad"})


def test_commit_for_dereferences_annotated_tag(upstream: Upstream, tmp_path: Path) -> None:
    clone = tmp_path / "clone"
    upstream.clone(clone)
    tag_object = git("rev-parse", "v1.0.0", cwd=upstream.path)
    commit = git("rev-parse", "v1.0.0^{commit}", cwd=upstream.path)

    assert tag_object != commit  # annotated: the tag is its own object
    assert up.commit_for(clone, "v1.0.0") == commit
