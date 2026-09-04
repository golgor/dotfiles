"""Decide what an update would do (`plan`), then do it (`execute`). No printing here."""

from dataclasses import dataclass, field
from pathlib import Path

from automation.skills import sync, upstream
from automation.skills.manifest import Manifest, Release, record_release


@dataclass(frozen=True)
class Plan:
    manifest: Manifest
    latest: Release
    up_to_date: bool
    to_sync: dict[str, Path] = field(default_factory=dict)  # selected name -> dir in the clone
    unselected: list[str] = field(default_factory=list)  # upstream skills not in the manifest
    orphans: list[Path] = field(default_factory=list)  # vendored dirs the manifest does not want
    missing_claude_entries: list[str] = field(default_factory=list)


def plan(root: Path, manifest: Manifest, clone: Path, latest: Release) -> Plan:
    """Inspect the locked and latest releases; raise AutomationError rather than plan
    anything that would overwrite a local fork or lose a skill.

    `clone` is a `--no-checkout` clone of the upstream repo; it is left at `latest`,
    so the returned `to_sync` paths stay valid while the clone exists.
    """
    locked = manifest.release

    if locked.commit:
        upstream.checkout(clone, locked.commit)
        in_locked = upstream.resolve_selected(
            upstream.discover_skills(clone), manifest.names(), missing_ok=True
        )
        sync.check_against_locked(root, manifest, in_locked)

    upstream.checkout(clone, latest.commit)
    found = upstream.discover_skills(clone)
    up_to_date = locked.commit == latest.commit and sync.all_present(root, manifest)

    to_sync: dict[str, Path] = {}
    if not up_to_date:
        to_sync = upstream.resolve_selected(found, manifest.names())
        upstream.validate_all(to_sync)

    return Plan(
        manifest=manifest,
        latest=latest,
        up_to_date=up_to_date,
        to_sync=to_sync,
        unselected=sorted(set(found) - set(manifest.selection)),
        orphans=sync.orphans(root, manifest, set(found)),
        missing_claude_entries=sync.missing_claude_entries(
            (root / "mise.toml").read_text(), manifest
        ),
    )


def execute(root: Path, manifest: Manifest, planned: Plan) -> list[Path]:
    """Copy every planned skill into place and record the release. Returns what was written."""
    written: list[Path] = []
    for name, src in planned.to_sync.items():
        dest = manifest.dest(root, name)
        sync.sync_skill(src, dest)
        written.append(dest.relative_to(root))
    record_release(manifest.path, planned.latest)
    return written
