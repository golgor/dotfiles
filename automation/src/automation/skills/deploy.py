"""Project skill directories as directory symlinks into every harness discovery directory.

Each harness (Pi, Claude Code, Codex) scans one directory under `home` for skills. This
module links `<discovery dir>/<name>` straight to `root/skills/<scope>/<name>` — a directory
symlink per skill, never a real directory of file symlinks. Codex's loader only follows
directory symlinks and ignores `SKILL.md` files that are themselves symlinks inside a real
directory, which is what mise's `symlink-each` produces; that is why this lives here instead.

Harness-owned neighbours (`hey`, `omarchy`, Codex's `.system/`, Claude's `synced/`) are never
real directories or symlinks pointing into `root/skills`, so they are left alone by construction:
only entries recognised as our own managed links are ever re-pointed or removed.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from automation import AutomationError
from automation.skills.manifest import SCOPE_DIRS, Scope


@dataclass(frozen=True)
class Harness:
    name: str  # human label used in messages, e.g. "Pi", "Claude Code", "Codex"
    directory: Path  # discovery dir relative to home, e.g. Path(".agents/skills")
    scopes: tuple[Scope, ...]


HARNESSES: tuple[Harness, ...] = (
    Harness("Pi", Path(".agents/skills"), ("common",)),
    Harness("Claude Code", Path(".claude/skills"), ("common", "claude")),
    Harness("Codex", Path(".codex/skills"), ("common",)),
)


@dataclass(frozen=True)
class Deployment:
    linked: list[Path]  # links created or re-pointed (the link path)
    pruned: list[Path]  # stale managed links removed
    unchanged: list[Path]  # already-correct links


@dataclass(frozen=True)
class _Plan:
    """What deploy_skills would do, computed across every harness before anything is written."""

    creates: list[tuple[Path, Path]] = field(default_factory=list)  # link -> target
    prunes: list[Path] = field(default_factory=list)
    unchanged: list[Path] = field(default_factory=list)
    conflicts: list[Path] = field(default_factory=list)


def _skill_dirs(root: Path, scope: Scope) -> dict[str, Path]:
    """Directories directly inside root/skills/<scope>, keyed by name. Missing scope -> empty."""
    scope_dir = root / SCOPE_DIRS[scope]
    if not scope_dir.is_dir():
        return {}
    return {p.name: p for p in scope_dir.iterdir() if p.is_dir()}


def _is_managed_link(link: Path, skills_root: Path) -> bool:
    """A symlink whose (possibly dangling) target sits inside skills_root.

    Deliberately reads the raw link target with readlink() instead of resolving it:
    we classify a link by where it *points*, not by what it resolves to, so a dangling
    link into a since-deleted skill is still recognisably ours to prune. The target is
    then normalised lexically (os.path.normpath) so a `..`-escaping target is not
    mistaken for one inside skills_root, and a relative target that legitimately points
    inside skills_root is recognised as managed.
    """
    if not link.is_symlink():
        return False
    target = link.readlink()
    if not target.is_absolute():
        target = link.parent / target
    target = Path(os.path.normpath(target.absolute()))
    return target.is_relative_to(skills_root)


def _desired_links(root: Path, home: Path, harness: Harness) -> dict[Path, Path]:
    """Link path -> target path for every skill this harness should see.

    Raises AutomationError if two scopes visible to this harness both contain a skill
    with the same name: the manifest layer permits that (scopes are keyed independently),
    but it would silently collapse into one deployed link here.
    """
    discovery = home / harness.directory
    desired: dict[Path, Path] = {}
    for scope in harness.scopes:
        for name, src in _skill_dirs(root, scope).items():
            link = discovery / name
            if link in desired:
                raise AutomationError(
                    f"skill {name!r} exists in two source directories visible to "
                    f"{harness.name}: {desired[link]} and {src}"
                )
            desired[link] = src
    return desired


def _check_discovery(discovery: Path) -> None:
    """A discovery path that exists as anything but a directory can never be deployed into.

    Checked during planning so the run fails before `_execute` creates any directory.
    `exists()` alone misses a dangling symlink (it follows the link and reports False,
    same as a path that is simply absent), so a symlink is also checked directly; a
    symlink to a real directory still passes, since that is a legitimate discovery dir.
    """
    if (discovery.exists() or discovery.is_symlink()) and not discovery.is_dir():
        raise AutomationError(
            f"cannot create skills discovery directory: {discovery} exists and is not a directory"
        )


def _plan(root: Path, home: Path) -> _Plan:
    """Decide what every harness needs, across all of them, without writing anything."""
    skills_root = (root / "skills").resolve()
    plan = _Plan()

    for harness in HARNESSES:
        discovery = home / harness.directory
        _check_discovery(discovery)
        desired = _desired_links(root, home, harness)

        for link, target in desired.items():
            if link.is_symlink():
                if not _is_managed_link(link, skills_root):
                    plan.conflicts.append(link)
                    continue
                if link.readlink() == target:
                    plan.unchanged.append(link)
                    continue
                plan.creates.append((link, target))
            elif link.exists():
                plan.conflicts.append(link)
            else:
                plan.creates.append((link, target))

        if not discovery.is_dir():
            continue  # nothing deployed there yet, so nothing to prune
        for entry in discovery.iterdir():
            if entry in desired:
                continue
            if _is_managed_link(entry, skills_root):
                plan.prunes.append(entry)

    return plan


def _execute(plan: _Plan) -> Deployment:
    """Apply an already-validated plan. Assumes plan.conflicts is empty."""
    linked: list[Path] = []
    for link, target in plan.creates:
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.is_symlink():
            link.unlink()
        link.symlink_to(target, target_is_directory=True)
        linked.append(link)

    pruned: list[Path] = []
    for entry in plan.prunes:
        entry.unlink()
        pruned.append(entry)

    return Deployment(linked=linked, pruned=pruned, unchanged=plan.unchanged)


def deploy_skills(root: Path, home: Path) -> Deployment:
    """Converge every harness discovery directory to one directory symlink per skill.

    Creates missing links, re-points managed links whose target moved, prunes managed
    links whose skill no longer exists, and leaves everything else untouched. Plans
    across every harness first; if any desired link path is occupied by something that
    is not a managed symlink, raises AutomationError listing every conflict before
    writing anything, so a run that hits one conflict leaves every harness untouched.
    """
    plan = _plan(root, home)

    if plan.conflicts:
        lines = [
            f"path occupied by something other than a managed skill link: {p}"
            for p in plan.conflicts
        ]
        raise AutomationError(
            "refusing to deploy skill links. Remove or move the conflicting path(s) by "
            "hand, then rerun\n  " + "\n  ".join(lines)
        )

    return _execute(plan)
