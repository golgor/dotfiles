from pathlib import Path

import pytest

from automation import AutomationError
from automation.skills.manifest import Release, load_manifest, record_release
from tests.helpers import Dotfiles


def test_load_maps_names_to_scopes(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"], claude=["beta"], tag="v1", commit="abc")
    manifest = load_manifest(dotfiles.manifest)

    assert manifest.repo == "example/skills"
    assert manifest.release == Release("v1", "abc")
    assert manifest.selection == {"alpha": "common", "beta": "claude"}
    assert manifest.dest(Path("/r"), "beta") == Path("/r/skills/claude/beta")


def test_unrecorded_release_is_empty_strings(dotfiles: Dotfiles) -> None:
    assert load_manifest(dotfiles.manifest).release == Release("", "")


def test_duplicate_across_scopes_rejected(dotfiles: Dotfiles) -> None:
    dotfiles.write_manifest(common=["alpha"], claude=["alpha"])
    with pytest.raises(AutomationError, match="two scopes: alpha"):
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
    before = dotfiles.manifest.read_text()
    record_release(dotfiles.manifest, Release("v2.0.0", "f" * 40))
    after = dotfiles.manifest.read_text()

    assert 'tag = "v2.0.0"' in after
    assert f'commit = "{"f" * 40}"' in after
    assert (
        after.replace('tag = "v2.0.0"', 'tag = ""').replace(f'commit = "{"f" * 40}"', 'commit = ""')
        == before
    )


def test_record_release_refuses_ambiguous_file(dotfiles: Dotfiles) -> None:
    dotfiles.manifest.write_text(dotfiles.manifest.read_text() + 'tag = "again"\n')
    with pytest.raises(AutomationError, match="exactly one `tag"):
        record_release(dotfiles.manifest, Release("v2", "abc"))
