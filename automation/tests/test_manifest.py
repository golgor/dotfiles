from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills.manifest import (
    Release,
    check_collisions,
    discover_manifests,
    load_manifest,
    record_release,
)
from tests.helpers import Dotfiles


def test_load_maps_names_to_scopes(dotfiles: Dotfiles) -> None:
    sha = "a" * 40
    dotfiles.write_manifest(common=["alpha"], claude=["beta"], tag="v1", commit=sha)
    manifest = load_manifest(dotfiles.manifest)

    assert manifest.name == "example"
    assert manifest.repo == "example/skills"
    assert manifest.branch is None
    assert manifest.release == Release(commit=sha, tag="v1")
    assert manifest.release.label() == f"release v1 ({sha[:12]})"
    assert manifest.selection == {"alpha": "common", "beta": "claude"}
    assert manifest.dest(Path("/r"), "beta") == Path("/r/skills/claude/beta")


def test_load_branch_manifest(dotfiles: Dotfiles) -> None:
    sha = "b" * 40
    dotfiles.write_manifest(
        "toolsense",
        repo="ToolSense/iot-claude-plugins",
        branch="main",
        common=["create-project"],
        commit=sha,
    )
    manifest = load_manifest(dotfiles.manifest_path("toolsense"))

    assert manifest.name == "toolsense"
    assert manifest.repo == "ToolSense/iot-claude-plugins"
    assert manifest.branch == "main"
    assert manifest.release == Release(commit=sha, tag="")
    assert manifest.release.label() == f"commit {sha[:12]}"
    assert manifest.selection == {"create-project": "common"}


def test_unrecorded_release_is_empty_strings(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"])
    assert load_manifest(dotfiles.manifest).release == Release(commit="", tag="")


def test_duplicate_across_scopes_rejected(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"], claude=["alpha"])
    with pytest.raises(AutomationError, match=r"two scopes in example\.toml: alpha"):
        load_manifest(dotfiles.manifest)


def test_unknown_scope_rejected(dotfiles: Dotfiles) -> None:
    dotfiles.manifest.write_text(
        'repo = "x"\n[release]\ntag = ""\ncommit = ""\n[scopes]\ncodex = []\n'
    )
    with pytest.raises(AutomationError, match="unknown scope"):
        load_manifest(dotfiles.manifest)


def test_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(AutomationError, match="missing manifest"):
        load_manifest(tmp_path / "nope.toml")


def test_record_release_rewrites_only_release_lines(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"])
    before = dotfiles.manifest.read_text()
    record_release(dotfiles.manifest, Release(commit="f" * 40, tag="v2.0.0"))
    after = dotfiles.manifest.read_text()

    assert 'tag = "v2.0.0"' in after
    assert f'commit = "{"f" * 40}"' in after
    assert (
        after.replace('tag = "v2.0.0"', 'tag = ""').replace(f'commit = "{"f" * 40}"', 'commit = ""')
        == before
    )


def test_record_release_for_branch_mode(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest("branch_repo", branch="main", common=["alpha"])
    record_release(dotfiles.manifest_path("branch_repo"), Release(commit="e" * 40, tag=""))
    after = dotfiles.manifest_path("branch_repo").read_text()

    assert f'commit = "{"e" * 40}"' in after
    assert 'tag = "' not in after


def test_record_release_refuses_ambiguous_file(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"])
    dotfiles.manifest.write_text(dotfiles.manifest.read_text() + 'commit = "again"\n')
    with pytest.raises(AutomationError, match="exactly one `commit"):
        record_release(dotfiles.manifest, Release(commit="abc", tag="v2"))


def test_malformed_toml_is_an_automation_error(dotfiles: Dotfiles) -> None:
    dotfiles.manifest.parent.mkdir(parents=True, exist_ok=True)
    dotfiles.manifest.write_text("repo = \n")
    with pytest.raises(AutomationError, match="invalid manifest"):
        load_manifest(dotfiles.manifest)


@pytest.mark.parametrize("repo", ["", "just-a-name", "owner/name/extra", "owner/na me", "-o/../x"])
def test_repo_must_be_owner_slash_name(dotfiles: Dotfiles, repo: str) -> None:
    dotfiles.manifest.parent.mkdir(parents=True, exist_ok=True)
    dotfiles.manifest.write_text(
        f'repo = "{repo}"\n[release]\ntag = ""\ncommit = ""\n[scopes]\ncommon = []\n'
    )
    with pytest.raises(AutomationError, match="owner/name"):
        load_manifest(dotfiles.manifest)


@pytest.mark.parametrize("branch", ["main", "feature/skills", "release/v2.0", "team/user/task"])
def test_valid_branch_names_with_slashes(dotfiles: Dotfiles, branch: str) -> None:
    dotfiles.write_manifest("branch_repo", branch=branch, common=["alpha"])
    manifest = load_manifest(dotfiles.manifest_path("branch_repo"))
    assert manifest.branch == branch


@pytest.mark.parametrize("branch", ["/leading", "trailing/", "double//slash", "has space"])
def test_invalid_branch_names_rejected(dotfiles: Dotfiles, branch: str) -> None:
    dotfiles.write_manifest("branch_repo", branch=branch, common=["alpha"])
    with pytest.raises(AutomationError, match="branch must be a valid ref name"):
        load_manifest(dotfiles.manifest_path("branch_repo"))


def test_empty_branch_name_rejected(dotfiles: Dotfiles) -> None:
    dotfiles.manifest.parent.mkdir(parents=True, exist_ok=True)
    dotfiles.manifest.write_text(
        'repo = "owner/repo"\nbranch = ""\n[release]\ncommit = ""\n[scopes]\ncommon = []\n'
    )
    with pytest.raises(AutomationError, match="branch must be a valid ref name"):
        load_manifest(dotfiles.manifest)


@pytest.mark.parametrize("tag_val", ["false", "[]", "123", "{ foo = 'bar' }"])
def test_non_string_release_tag_rejected(dotfiles: Dotfiles, tag_val: str) -> None:
    dotfiles.manifest.parent.mkdir(parents=True, exist_ok=True)
    dotfiles.manifest.write_text(
        f'repo = "owner/repo"\n[release]\ntag = {tag_val}\ncommit = ""\n[scopes]\ncommon = []\n'
    )
    with pytest.raises(AutomationError, match=r"release\.tag must be a string"):
        load_manifest(dotfiles.manifest)


@pytest.mark.parametrize("commit", ["abc", "--detach", "g" * 40, "A" * 40])
def test_commit_must_be_full_lowercase_sha_or_empty(dotfiles: Dotfiles, commit: str) -> None:
    dotfiles.write_manifest(common=["alpha"], tag="v1", commit=commit)
    with pytest.raises(AutomationError, match="40-hex SHA"):
        load_manifest(dotfiles.manifest)


def test_discover_manifests_finds_and_loads_all(dotfiles: Dotfiles) -> None:
    dotfiles.manifest.unlink()
    dotfiles.write_manifest("first", common=["alpha"])
    dotfiles.write_manifest("second", common=["beta"])
    manifests = discover_manifests(dotfiles.root)

    assert [m.name for m in manifests] == ["first", "second"]


def test_check_collisions_flags_duplicate_skill_in_same_scope(
    dotfiles: Dotfiles,
) -> None:
    dotfiles.manifest.unlink()
    m1 = load_manifest(dotfiles.write_manifest("first", common=["alpha", "beta"]))
    m2 = load_manifest(dotfiles.write_manifest("second", common=["beta", "gamma"]))

    with pytest.raises(AutomationError) as exc:
        check_collisions([m1, m2])
    assert "skill 'beta' in scope 'common' is claimed by both 'first' and 'second'" in str(
        exc.value
    )
