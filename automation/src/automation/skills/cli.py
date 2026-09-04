"""`skills update`: refresh the vendored mattpocock/skills snapshot from the latest release.

Manual task: needs network access (gh + git) and rewrites tracked skill
directories. It never commits or pushes; review the diff and open a PR.
"""

import argparse
import io
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from automation import AutomationError
from automation.process import git_root, run, stream
from automation.skills import sync, update
from automation.skills.manifest import MANIFEST, SCOPE_DIRS, load_manifest
from automation.skills.upstream import GitHubReleases, ReleaseSource

Apply = Callable[[Path], None]
SourceFor = Callable[[str], ReleaseSource]  # "owner/name" -> where its releases come from


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
    source_for: SourceFor = GitHubReleases,
    apply: Apply = apply_dotfiles,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> None:
    manifest = load_manifest(root / MANIFEST)
    sync.require_clean(root)

    source = source_for(manifest.repo)
    latest_tag = source.latest_tag()
    print(f"Latest release of {manifest.repo}: {latest_tag}", file=out)
    if manifest.release.commit:
        print(
            f"Checking vendored skills against locked release {manifest.release.tag}...", file=out
        )
    else:
        print("No locked release yet; skipping divergence check for this first import.", file=out)

    with tempfile.TemporaryDirectory(prefix="matt-skills.") as tmp:
        clone = Path(tmp) / "repo"
        source.clone(clone)
        planned = update.plan(root, manifest, clone, latest_tag)
        print_warnings(planned, err)

        if planned.up_to_date:
            print(
                f"Already at {latest_tag} ({planned.latest.commit[:12]}); nothing to do.", file=out
            )
            return

        release = f"{latest_tag} ({planned.latest.commit[:12]})"
        print(f"Syncing {len(planned.to_sync)} skills from {release}...", file=out)
        for path in update.execute(root, manifest, planned):
            print(f"  {path}", file=out)

    if planned.unselected:
        print(f"Available upstream but not selected ({len(planned.unselected)}):", file=out)
        for name in planned.unselected:
            print(f"  {name}", file=out)

    print("Re-applying dotfile symlinks...", file=out)
    apply(root)
    print_git_summary(root, out)


def print_warnings(planned: update.Plan, err: TextIO) -> None:
    for path in planned.orphans:
        print(
            f"warning: {path} matches an upstream skill but is not selected; "
            "delete it or add it back to the manifest",
            file=err,
        )
    for name in planned.missing_claude_entries:
        print(
            f"warning: {name} is Claude-only but mise.toml has no entry for skills/claude/{name}; "
            "it will not be deployed until one is added",
            file=err,
        )


def print_git_summary(root: Path, out: TextIO) -> None:
    changed = [str(MANIFEST), *(str(p) for p in SCOPE_DIRS.values())]
    print(file=out)
    print(run("git", "status", "--short", "--", *changed, cwd=root), file=out)
    print(file=out)
    print(run("git", "diff", "--stat", "--", *changed, cwd=root), file=out)
    print(file=out)
    print("Review the changes, then commit them on a branch and open a PR.", file=out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skills", description="Manage skills vendored from mattpocock/skills."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "update",
        help="sync selected skills from the latest upstream release",
        description=(
            "Sync the skills selected in .mise/skills/mattpocock.toml from the latest GitHub "
            "release of mattpocock/skills into skills/common/ and skills/claude/, record the "
            "release, and re-apply dotfile symlinks. Refuses to run over uncommitted vendored "
            "directories or vendored skills that no longer match the locked release. Never commits."
        ),
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
            run_update(root)
    except AutomationError as e:
        print(f"skills {args.command}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
