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

from dataclasses import dataclass
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


def _skill_dirs(root: Path, scope: Scope) -> dict[str, Path]:
    """Directories directly inside root/skills/<scope>, keyed by name. Missing scope -> empty."""
    scope_dir = root / SCOPE_DIRS[scope]
    if not scope_dir.is_dir():
        return {}
    return {p.name: p for p in scope_dir.iterdir() if p.is_dir()}


def _is_managed_link(link: Path, root: Path) -> bool:
    """A symlink whose (possibly dangling) target sits inside root/skills.

    Deliberately reads the raw link target instead of resolving it: a skill directory
    that was deleted upstream still leaves a dangling link we must recognise as ours
    to prune, and resolve() on a dangling link would raise or misbehave.
    """
    if not link.is_symlink():
        return False
    target = link.readlink()
    if not target.is_absolute():
        target = (link.parent / target).absolute()
    return target.is_relative_to(root / "skills")


def _desired_links(root: Path, home: Path, harness: Harness) -> dict[Path, Path]:
    """Link path -> target path for every skill this harness should see."""
    discovery = home / harness.directory
    desired: dict[Path, Path] = {}
    for scope in harness.scopes:
        for name, src in _skill_dirs(root, scope).items():
            desired[discovery / name] = src
    return desired


def deploy_skills(root: Path, home: Path, harnesses: tuple[Harness, ...] = HARNESSES) -> Deployment:
    """Converge every harness discovery directory to one directory symlink per skill.

    Creates missing links, re-points managed links whose target moved, prunes managed
    links whose skill no longer exists, and leaves everything else untouched. Raises
    AutomationError, listing every conflict, if a desired link path is occupied by
    something that is not a managed symlink. Conflicts are collected across every
    harness and raised together at the end, so a run that hits one may already have
    created or pruned links elsewhere.
    """
    linked: list[Path] = []
    unchanged: list[Path] = []
    pruned: list[Path] = []
    conflicts: list[Path] = []

    for harness in harnesses:
        discovery = home / harness.directory
        discovery.mkdir(parents=True, exist_ok=True)
        desired = _desired_links(root, home, harness)

        for link, target in desired.items():
            if link.is_symlink():
                if not _is_managed_link(link, root):
                    conflicts.append(link)
                    continue
                if link.readlink() == target:
                    unchanged.append(link)
                    continue
                link.unlink()
            elif link.exists():
                conflicts.append(link)
                continue
            link.symlink_to(target, target_is_directory=True)
            linked.append(link)

        for entry in discovery.iterdir():
            if entry in desired:
                continue
            if _is_managed_link(entry, root):
                entry.unlink()
                pruned.append(entry)

    if conflicts:
        lines = [
            f"path occupied by something other than a managed skill link: {p}" for p in conflicts
        ]
        raise AutomationError(
            "refusing to deploy skill links. Remove or move the conflicting path(s) by "
            "hand, then rerun\n  " + "\n  ".join(lines)
        )

    return Deployment(linked=linked, pruned=pruned, unchanged=unchanged)
