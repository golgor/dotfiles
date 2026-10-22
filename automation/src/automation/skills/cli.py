"""Project locally maintained agent skills into harness discovery directories."""

import argparse
import io
import sys
from pathlib import Path
from typing import TextIO

from automation import AutomationError
from automation.process import git_root
from automation.skills.deploy import Deployment, deploy_skills


def default_deploy(root: Path, out: TextIO = sys.stdout) -> None:
    """Project skill directory symlinks into every harness and print what changed."""
    print_deployment(deploy_skills(root, Path.home()), out)


def print_deployment(deployment: Deployment, out: TextIO = sys.stdout) -> None:
    if not (deployment.linked or deployment.pruned or deployment.unchanged):
        print("Nothing to do; no skills found to deploy.", file=out)
        return
    for path in deployment.linked:
        print(f"  linked {path}", file=out)
    for path in deployment.pruned:
        print(f"  pruned {path}", file=out)
    if deployment.unchanged:
        print(f"{len(deployment.unchanged)} link(s) already up to date.", file=out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skills", description="Deploy locally maintained agent skills."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "deploy",
        help="project skill directory symlinks into Pi, Claude Code, and Codex",
        description=(
            "Project one directory symlink per skill from skills/common/ and skills/claude/ "
            "into ~/.agents/skills (Pi), ~/.claude/skills (Claude Code), and ~/.codex/skills "
            "(Codex). Creates missing links, re-points moved ones, and prunes links whose "
            "skill no longer exists. Leaves harness-owned neighbours untouched and refuses "
            "to overwrite any path that is not already a symlink pointing into skills/."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)  # keep our lines ordered with mise's output
    args = build_parser().parse_args(argv)
    try:
        root = git_root()
        if not (root / "mise.toml").is_file():
            raise AutomationError(f"{root} does not look like the dotfiles repository")
        default_deploy(root)
    except AutomationError as e:
        print(f"skills {args.command}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
