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

import fcntl
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Literal

from automation import AutomationError

Scope = Literal["common", "claude", "matt", "pstack"]
Stack = Literal["matt", "pstack"]
SCOPE_DIRS: dict[Scope, Path] = {
    "common": Path("skills/common"),
    "claude": Path("skills/claude"),
    "matt": Path("skills/matt"),
    "pstack": Path("skills/pstack"),
}
STACKS: tuple[Stack, ...] = ("matt", "pstack")


@dataclass(frozen=True)
class Harness:
    name: str  # human label used in messages, e.g. "Pi", "Claude Code", "Codex"
    directory: Path  # discovery dir relative to home, e.g. Path(".agents/skills")
    scopes: tuple[Scope, ...]


def _validate_stack(stack: str) -> Stack:
    if stack not in STACKS:
        raise AutomationError(f"unknown skill stack {stack!r}; choose matt or pstack")
    return stack


# Kept public for callers and tests that inspect the three harness destinations.
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
    """Directories directly inside root/skills/<scope>, keyed by name."""
    scope_dir = root / SCOPE_DIRS[scope]
    if not scope_dir.is_dir():
        return {}
    return {p.name: p for p in scope_dir.iterdir() if p.is_dir()}


class _Occupancy(Enum):
    """What is at a path, and whether it is ours to touch."""

    FREE = auto()  # nothing at this path
    MANAGED = auto()  # a symlink of ours: target normalises to inside skills_root
    FOREIGN = auto()  # a real file, a real directory, or a symlink pointing elsewhere


def _classify(path: Path, skills_root: Path) -> _Occupancy:
    """Classify what is at path with respect to skills_root.

    FOREIGN is never touched: a real file, a real directory, or a symlink whose target
    lies outside skills_root. MANAGED is ours to re-point or prune, even when its target
    no longer exists — a dangling link into a since-deleted skill is still ours.

    That is why the raw link target is read with readlink() rather than resolved: a link
    is classified by where it *points*, not by what it resolves to. The target is then
    normalised lexically (os.path.normpath) so a `..`-escaping target is not mistaken
    for one inside skills_root, and a relative target that legitimately points inside
    skills_root is recognised as managed.
    """
    if not path.is_symlink():
        return _Occupancy.FREE if not path.exists() else _Occupancy.FOREIGN
    target = path.readlink()
    if not target.is_absolute():
        target = path.parent / target
    target = Path(os.path.normpath(target.absolute()))
    return _Occupancy.MANAGED if target.is_relative_to(skills_root) else _Occupancy.FOREIGN


def _desired_links(root: Path, home: Path, harness: Harness) -> dict[Path, Path]:
    """Link path -> target path for every skill this harness should see.

    Raises AutomationError if two scopes visible to this harness both contain a skill
    with the same name: it would silently collapse into one deployed link here.
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


def _check_discovery(discovery: Path, skills_root: Path) -> None:
    """A discovery path that exists as anything but a directory can never be deployed into.

    Checked during planning so the run fails before `_execute` creates any directory.
    A discovery path classifies as FREE (nothing there) or a symlink to a real
    directory, both fine; anything else — including a dangling symlink, which
    `exists()` alone would miss — is refused.
    """
    if _classify(discovery, skills_root) is not _Occupancy.FREE and not discovery.is_dir():
        raise AutomationError(
            f"cannot create skills discovery directory: {discovery} exists and is not a directory"
        )


def _plan(root: Path, home: Path, stack: str) -> _Plan:
    """Decide what every harness needs, across all of them, without writing anything."""
    selected_stack = _validate_stack(stack)
    selected_dir = root / SCOPE_DIRS[selected_stack]
    if not selected_dir.is_dir():
        raise AutomationError(f"selected skill stack {stack!r} does not exist: {selected_dir}")
    skills_root = (root / "skills").resolve()
    harnesses = tuple(
        Harness(harness.name, harness.directory, (*harness.scopes, selected_stack))
        for harness in HARNESSES
    )
    plan = _Plan()

    for harness in harnesses:
        discovery = home / harness.directory
        _check_discovery(discovery, skills_root)
        desired = _desired_links(root, home, harness)

        for link, target in desired.items():
            occupancy = _classify(link, skills_root)
            if occupancy is _Occupancy.FOREIGN:
                plan.conflicts.append(link)
            elif occupancy is _Occupancy.FREE:
                plan.creates.append((link, target))
            elif link.readlink() == target:
                plan.unchanged.append(link)
            else:
                plan.creates.append((link, target))

        if not discovery.is_dir():
            continue  # nothing deployed there yet, so nothing to prune
        for entry in discovery.iterdir():
            if entry in desired:
                continue
            if _classify(entry, skills_root) is _Occupancy.MANAGED:
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


@contextmanager
def _deployment_lock(home: Path):
    """Serialize planning and execution for deployments targeting one home.

    The lock file is deliberately stable and outside all harness discovery directories;
    creating its parent and the lock file are the only home mutations before planning.
    This coordinates cooperating deployers; it does not make filesystem operations
    transactional or roll them back after an interruption or runtime error.
    """
    lock_path = home / ".local/state/automation/skills-deploy.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def deploy_skills(root: Path, home: Path, stack: str = "matt") -> Deployment:
    """Converge every harness discovery directory to one directory symlink per skill.

    A home-scoped lock serializes planning, conflict checking, and execution across
    stack selections and checkout roots targeting this home. Creates missing links,
    re-points managed links whose target moved, prunes managed links whose skill no
    longer exists, and leaves everything else untouched. Plans across every harness
    first; if any desired link path is occupied by something that is not a managed
    symlink, raises AutomationError listing every conflict before changing any harness
    discovery link. The lock parent and file persist even when preflight rejects the
    deployment. That preflight safety is not transactional execution: runtime errors or
    interruptions can leave partial work, and rerunning the desired stack converges.
    """
    with _deployment_lock(home):
        plan = _plan(root, home, stack)

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
