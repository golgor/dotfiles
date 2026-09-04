"""Compare and copy vendored skill directories. Returns findings; the CLI decides what to print."""

import filecmp
import shutil
from pathlib import Path

from automation import AutomationError
from automation.process import run
from automation.skills.manifest import SCOPE_DIRS, Manifest


def require_clean(root: Path) -> None:
    """Vendored directories must be committed. The manifest may be dirty: editing its
    selection and then running the updater is the normal workflow."""
    paths = [str(p) for p in SCOPE_DIRS.values()]
    dirty = run("git", "status", "--porcelain", "--", *paths, cwd=root)
    if dirty:
        raise AutomationError(
            "uncommitted changes under managed skill paths; commit or stash them first\n" + dirty
        )


def trees_differ(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b, ignore=[])
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return True
    _, mismatch, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    if mismatch or errors:
        return True
    return any(trees_differ(a / d, b / d) for d in cmp.common_dirs)


def check_against_locked(
    root: Path, manifest: Manifest, locked_upstream: dict[str, list[Path]]
) -> None:
    """Every existing vendored skill must equal the locked release's copy.

    Vendored skills are immutable snapshots: a local edit is a fork and belongs
    under a new name outside the manifest selection.
    """
    divergent: list[Path] = []
    unmanaged: list[Path] = []
    for name in manifest.names():
        dest = manifest.dest(root, name)
        if not dest.exists():
            continue
        if name not in locked_upstream:
            unmanaged.append(dest.relative_to(root))
        elif trees_differ(dest, locked_upstream[name][0]):
            divergent.append(dest.relative_to(root))

    if divergent or unmanaged:
        lines = [f"differs from locked release: {p}" for p in divergent]
        lines += [f"exists locally but not in locked release: {p}" for p in unmanaged]
        raise AutomationError(
            "refusing to overwrite. Vendored skills are immutable snapshots: restore with "
            "`git checkout -- <path>`, or move your fork to a new name outside the manifest "
            "selection\n  " + "\n  ".join(lines)
        )


def all_present(root: Path, manifest: Manifest) -> bool:
    return all(manifest.dest(root, n).exists() for n in manifest.names())


def sync_skill(src: Path, dest: Path) -> None:
    """Verbatim copy, deleting anything not upstream; copy2 keeps executable bits."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, symlinks=True)


def orphans(root: Path, manifest: Manifest, upstream_names: set[str]) -> list[Path]:
    """Vendored directories whose name is upstream but no longer selected."""
    return sorted(
        scope_dir / n
        for scope_dir in SCOPE_DIRS.values()
        for n in upstream_names - set(manifest.selection)
        if (root / scope_dir / n).is_dir()
    )


def missing_claude_entries(mise_toml: str, manifest: Manifest) -> list[str]:
    """Claude-only skills need their own whole-directory entry in mise.toml to deploy."""
    return sorted(
        n
        for n, scope in manifest.selection.items()
        if scope == "claude" and f"skills/claude/{n}" not in mise_toml
    )
