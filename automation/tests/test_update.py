"""`plan()` decides; `execute()` writes. Tested against the fixture repos, no CLI."""

from pathlib import Path

from automation.skills import update
from automation.skills.manifest import load_manifest
from tests.helpers import Dotfiles, Upstream, write_skill


def clone_of(upstream: Upstream, tmp_path: Path) -> Path:
    clone = tmp_path / "clone"
    upstream.clone(clone)
    return clone


def test_plan_first_import(dotfiles: Dotfiles, upstream: Upstream, tmp_path: Path) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    manifest = load_manifest(dotfiles.manifest)
    clone = clone_of(upstream, tmp_path)
    latest = upstream.resolve_latest(clone)
    planned = update.plan(dotfiles.root, manifest, clone, latest)

    assert not planned.up_to_date
    assert set(planned.to_sync) == {"alpha", "beta"}
    assert planned.unselected == ["extra"]
    assert planned.orphans == []
    assert planned.latest.tag == "v1.0.0"


def test_plan_up_to_date_still_reports_orphans(
    dotfiles: Dotfiles, upstream: Upstream, tmp_path: Path
) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    clone = clone_of(upstream, tmp_path)
    manifest = load_manifest(dotfiles.manifest)
    latest = upstream.resolve_latest(clone)
    update.execute(dotfiles.root, manifest, update.plan(dotfiles.root, manifest, clone, latest))
    write_skill(dotfiles.root / "skills/common/extra", "extra")  # not selected
    manifest = load_manifest(dotfiles.manifest)  # now carries the recorded release

    planned = update.plan(dotfiles.root, manifest, clone, latest)

    assert planned.up_to_date
    assert planned.to_sync == {}
    assert planned.orphans == [Path("skills/common/extra")]


def test_execute_writes_and_records(dotfiles: Dotfiles, upstream: Upstream, tmp_path: Path) -> None:
    dotfiles.write_manifest(common=["alpha", "beta"])
    manifest = load_manifest(dotfiles.manifest)
    clone = clone_of(upstream, tmp_path)
    latest = upstream.resolve_latest(clone)
    planned = update.plan(dotfiles.root, manifest, clone, latest)

    written = update.execute(dotfiles.root, manifest, planned)

    assert written == [Path("skills/common/alpha"), Path("skills/common/beta")]
    assert (dotfiles.root / "skills/common/alpha/agents/openai.yaml").exists()
    assert load_manifest(dotfiles.manifest).release == planned.latest
