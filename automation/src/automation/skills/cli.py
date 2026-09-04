"""`skills update`: refresh the vendored mattpocock/skills snapshot from the latest release.

Manual task: needs network access (gh + git) and rewrites tracked skill
directories. It never commits or pushes; review the diff and open a PR.
"""

import argparse
import io
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from automation import AutomationError
from automation.process import git_root, run
from automation.skills import sync, upstream
from automation.skills.manifest import MANIFEST, SCOPE_DIRS, Release, load_manifest, record_release
from automation.skills.upstream import GitHubReleases, ReleaseSource

Apply = Callable[[Path], None]
SourceFor = Callable[[str], ReleaseSource]  # "owner/name" -> where its releases come from


def apply_dotfiles(root: Path) -> None:
    """`mise bootstrap dotfiles apply` so new/deleted files are live.

    mise 2026.9.1 can fail with ENOENT while pruning parents of stale links when a
    removed skill had files at two depths (SKILL.md + agents/openai.yaml). The links
    are already gone by then; a second apply converges cleanly.
    """
    cmd = ["mise", "bootstrap", "dotfiles", "apply", "-y"]
    if subprocess.run(cmd, cwd=root, check=False).returncode != 0:
        print("apply failed once; retrying", file=sys.stderr)
        if subprocess.run(cmd, cwd=root, check=False).returncode != 0:
            raise AutomationError(
                "`mise bootstrap dotfiles apply` failed twice; see its output above"
            )


def update(
    root: Path,
    source_for: SourceFor = GitHubReleases,
    apply: Apply = apply_dotfiles,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> None:
    manifest_path = root / MANIFEST
    manifest = load_manifest(manifest_path)
    sync.require_clean(root)

    source = source_for(manifest.repo)
    latest_tag = source.latest_tag()
    print(f"Latest release of {manifest.repo}: {latest_tag}", file=out)

    with tempfile.TemporaryDirectory(prefix="matt-skills.") as tmp:
        clone = Path(tmp) / "repo"
        source.clone(clone)
        latest = Release(tag=latest_tag, commit=upstream.commit_for(clone, latest_tag))

        locked = manifest.release
        if locked.commit:
            print(f"Checking vendored skills against locked release {locked.tag}...", file=out)
            upstream.checkout(clone, locked.commit)
            in_locked = upstream.resolve_selected(
                upstream.discover_skills(clone), manifest.names(), missing_ok=True
            )
            sync.check_against_locked(root, manifest, in_locked)
        else:
            print(
                "No locked release yet; skipping divergence check for this first import.", file=out
            )

        upstream.checkout(clone, latest.commit)
        found = upstream.discover_skills(clone)
        for path in sync.orphans(root, manifest, set(found)):
            print(
                f"warning: {path} matches an upstream skill but is not selected; "
                "delete it or add it back to the manifest",
                file=err,
            )

        if locked.commit == latest.commit and sync.all_present(root, manifest):
            print(f"Already at {latest.tag} ({latest.commit[:12]}); nothing to do.", file=out)
            return

        selected = upstream.resolve_selected(found, manifest.names())
        upstream.validate_all(selected)

        print(
            f"Syncing {len(selected)} skills from {latest.tag} ({latest.commit[:12]})...", file=out
        )
        for name, src in selected.items():
            dest = manifest.dest(root, name)
            sync.sync_skill(src, dest)
            print(f"  {dest.relative_to(root)}", file=out)

        unselected = sorted(set(found) - set(manifest.selection))
        if unselected:
            print(f"Available upstream but not selected ({len(unselected)}):", file=out)
            for name in unselected:
                print(f"  {name}", file=out)

    record_release(manifest_path, latest)
    for name in sync.missing_claude_entries((root / "mise.toml").read_text(), manifest):
        print(
            f"warning: {name} is Claude-only but mise.toml has no entry for skills/claude/{name}; "
            "it will not be deployed until one is added",
            file=err,
        )

    print("Re-applying dotfile symlinks...", file=out)
    apply(root)

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
            update(root)
    except AutomationError as e:
        print(f"skills {args.command}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
