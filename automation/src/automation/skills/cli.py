"""Project locally maintained agent skills into harness discovery directories."""

import argparse
import io
import sys
from pathlib import Path
from typing import TextIO

from automation import AutomationError
from automation.process import git_root
from automation.skills.deploy import Deployment, deploy_skills


def default_deploy(root: Path, out: TextIO = sys.stdout, stack: str = "matt") -> None:
    """Project the selected skill stack into every harness and print what changed."""
    print(f"Deploying {stack} skill stack.", file=out)
    print_deployment(deploy_skills(root, Path.home(), stack=stack), out, root=root, stack=stack)


def _skill_names(paths: list[Path]) -> set[str]:
    return {path.name for path in paths}


def _source_names(root: Path, scope: str) -> set[str]:
    source = root / "skills" / scope
    if not source.is_dir():
        return set()
    return {path.name for path in source.iterdir() if path.is_dir()}


def _report_counts(deployment: Deployment, source_names: set[str]) -> tuple[int, int]:
    linked = _skill_names(deployment.linked) & source_names
    unchanged = (_skill_names(deployment.unchanged) & source_names) - linked
    return len(linked), len(unchanged)


def _skills_word(count: int) -> str:
    return "skill" if count == 1 else "skills"


def print_deployment(
    deployment: Deployment,
    out: TextIO = sys.stdout,
    *,
    root: Path,
    stack: str = "matt",
) -> None:
    if not (deployment.linked or deployment.pruned or deployment.unchanged):
        print("Nothing to do; no skills found to deploy.", file=out)
        return

    selected = _source_names(root, stack)
    shared = _source_names(root, "common") | _source_names(root, "claude")
    linked, unchanged = _report_counts(deployment, selected)
    print(
        f"{stack}: {linked} {_skills_word(linked)} linked, {unchanged} already up to date.",
        file=out,
    )
    linked, unchanged = _report_counts(deployment, shared)
    print(
        f"Common/Claude extras: {linked} {_skills_word(linked)} linked, "
        f"{unchanged} already up to date.",
        file=out,
    )
    pruned = len(_skill_names(deployment.pruned))
    print(f"Stale links removed for {pruned} {_skills_word(pruned)}.", file=out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skills", description="Deploy locally maintained agent skills."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "deploy",
        help="project skill directory symlinks into Pi, Claude Code, and Codex",
        description=(
            "Project one directory symlink per skill from skills/common/, the selected stack, "
            "and skills/claude/ into the harness discovery directories. Creates missing links, "
            "re-points moved ones, and prunes inactive stack links. Leaves harness-owned "
            "neighbours untouched and refuses to overwrite any path that is not already a "
            "symlink pointing into skills/."
        ),
    )
    sub.choices["deploy"].add_argument(
        "--stack",
        choices=("matt", "pstack"),
        default="matt",
        help="stack-specific skills to deploy (default: matt)",
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
        default_deploy(root, stack=args.stack)
    except AutomationError as e:
        print(f"skills {args.command}: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
