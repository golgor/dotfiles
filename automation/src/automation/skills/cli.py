"""`skills update`: refresh vendored skills from upstream releases or branches.

Manual task: needs network access (gh + git) and rewrites tracked skill
directories. It never commits or pushes; review the diff and open a PR.
"""

import argparse
import contextlib
import io
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from automation import AutomationError
from automation.process import git_root, run, stream
from automation.skills import sync, update
from automation.skills.manifest import (
    MANIFESTS_DIR,
    SCOPE_DIRS,
    Manifest,
    discover_manifests,
)
from automation.skills.upstream import GitHubUpstream, ReleaseSource

Apply = Callable[[Path], None]
SourceFor = Callable[[Manifest], ReleaseSource]


def default_source(manifest: Manifest) -> ReleaseSource:
    return GitHubUpstream(repo=manifest.repo, branch=manifest.branch)


def apply_dotfiles(root: Path) -> None:
    """`mise bootstrap dotfiles apply` so new/deleted files are live.

    mise 2026.9.1 can fail with ENOENT while pruning parents of stale links when a
    removed skill had files at two depths (SKILL.md + agents/openai.yaml). The links
    are already gone by then; a second apply converges cleanly.
    """
    cmd = ("mise", "bootstrap", "dotfiles", "apply", "-y")
    if stream(*cmd, cwd=root) != 0:
        print("apply failed once; retrying", file=sys.stderr)
        if stream(*cmd, cwd=root) != 0:
            raise AutomationError(
                "`mise bootstrap dotfiles apply` failed twice; see its output above"
            )


def run_update(
    root: Path,
    target_name: str | None = None,
    source_for: SourceFor = default_source,
    apply: Apply = apply_dotfiles,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> bool:
    sync.require_clean(root)
    all_manifests = discover_manifests(root)

    if target_name:
        clean_name = target_name.removesuffix(".toml")
        targets = [m for m in all_manifests if m.name == clean_name]
        if not targets:
            avail = ", ".join(m.name for m in all_manifests)
            raise AutomationError(f"manifest {target_name!r} not found. Available: {avail}")
    else:
        targets = all_manifests

    # Phase 1: Plan all targets. If any manifest fails (divergence, integrity, etc.),
    # we fail immediately before writing any files to disk.
    plans: list[tuple[Manifest, update.Plan]] = []
    with contextlib.ExitStack() as stack:
        for manifest in targets:
            source = source_for(manifest)
            label_target = source.label()
            prefix = f"[{manifest.name}] " if len(targets) > 1 else ""

            print(f"{prefix}Latest target of {manifest.repo}: {label_target}", file=out)
            if manifest.release.commit:
                lbl = manifest.release.label()
                print(f"{prefix}Checking vendored skills against locked {lbl}...", file=out)
            else:
                msg = (
                    f"{prefix}No locked release yet; skipping divergence check "
                    "for this first import."
                )
                print(msg, file=out)

            tmp_dir = stack.enter_context(
                tempfile.TemporaryDirectory(prefix=f"{manifest.name}-skills.")
            )
            clone = Path(tmp_dir) / "repo"
            source.clone(clone)
            latest = source.resolve_latest(clone)
            planned = update.plan(root, manifest, all_manifests, clone, latest)
            print_warnings(planned, err, prefix)
            plans.append((manifest, planned))

        # Phase 2: Execute all validated plans.
        any_changed = False
        for manifest, planned in plans:
            prefix = f"[{manifest.name}] " if len(targets) > 1 else ""
            if planned.up_to_date:
                print(f"{prefix}Already at {planned.latest.label()}; nothing to do.", file=out)
                continue

            any_changed = True
            release_label = planned.latest.label()
            print(
                f"{prefix}Syncing {len(planned.to_sync)} skills from {release_label}...",
                file=out,
            )
            for path in update.execute(root, manifest, planned):
                print(f"  {path}", file=out)

            if planned.unselected:
                print(
                    f"{prefix}Available upstream but not selected ({len(planned.unselected)}):",
                    file=out,
                )
                for name in planned.unselected:
                    print(f"  {name}", file=out)

        if any_changed:
            print("Re-applying dotfile symlinks...", file=out)
            apply(root)
            print_git_summary(root, out)
    return any_changed


def print_warnings(planned: update.Plan, err: TextIO, prefix: str = "") -> None:
    for path in planned.orphans:
        print(
            f"{prefix}warning: {path} matches an upstream skill but is not selected; "
            "delete it or add it back to the manifest",
            file=err,
        )
    for name in planned.missing_claude_entries:
        warning = (
            f"{prefix}warning: {name} is Claude-only but mise.toml has no entry for "
            f"skills/claude/{name}; it will not be deployed until one is added"
        )
        print(warning, file=err)


def print_git_summary(root: Path, out: TextIO) -> None:
    manifest_paths = [str(p) for p in (root / MANIFESTS_DIR).glob("*.toml")]
    changed = [*manifest_paths, *(str(p) for p in SCOPE_DIRS.values())]
    print(file=out)
    print(run("git", "status", "--short", "--", *changed, cwd=root), file=out)
    print(file=out)
    print(run("git", "diff", "--stat", "--", *changed, cwd=root), file=out)
    print(file=out)
    print("Review the changes, then commit them on a branch and open a PR.", file=out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skills", description="Manage skills vendored from upstream git repositories."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    update_cmd = sub.add_parser(
        "update",
        help="sync selected skills from upstream manifests in .mise/skills/*.toml",
        description=(
            "Sync skills selected in manifests under .mise/skills/*.toml into skills/common/ "
            "and skills/claude/, record the updated release/branch commit, and re-apply dotfile "
            "symlinks. Refuses to run over uncommitted vendored directories or vendored skills "
            "that no longer match the locked release. Never commits."
        ),
    )
    update_cmd.add_argument(
        "manifest",
        nargs="?",
        default=None,
        help="Optional manifest name to update (default: all manifests in .mise/skills/*.toml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)  # keep our lines ordered with mise's output
    args = build_parser().parse_args(argv)
    try:
        if args.command == "update":
            root = git_root()
            if not (root / "mise.toml").is_file():
                raise AutomationError(f"{root} does not look like the dotfiles repository")
            run_update(root, target_name=args.manifest)
    except AutomationError as e:
        print(f"skills {args.command}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
