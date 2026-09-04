"""The upstream skills repository: where releases come from and what a valid skill looks like."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from automation import AutomationError
from automation.process import run
from automation.skills.manifest import Release


class ReleaseSource(Protocol):
    """Where releases come from. GitHub / git remote in production; a local repo in tests."""

    def resolve_latest(self, clone: Path) -> Release:
        """Resolve the latest Release using the clone."""
        ...

    def clone(self, dest: Path) -> None:
        """Clone without checking out; callers use `checkout` to pick a ref."""
        ...


@dataclass(frozen=True)
class GitHubUpstream:
    repo: str  # "owner/name"
    branch: str | None = None  # None -> tracks latest GitHub release tag

    def resolve_latest(self, clone: Path) -> Release:
        if self.branch:
            commit = run("git", "rev-parse", f"origin/{self.branch}^{{commit}}", cwd=clone)
            return Release(commit=commit, tag="")
        tag = run("gh", "api", f"repos/{self.repo}/releases/latest", "--jq", ".tag_name")
        commit = commit_for(clone, tag)
        return Release(commit=commit, tag=tag)

    def clone(self, dest: Path) -> None:
        run("git", "clone", "-q", "--no-checkout", f"https://github.com/{self.repo}.git", str(dest))


def commit_for(clone: Path, tag: str) -> str:
    """Full commit SHA for a tag, dereferencing annotated tags. The refs/tags/ form keeps
    a tag name from ever being read as an option."""
    return run("git", "rev-parse", f"refs/tags/{tag}^{{commit}}", cwd=clone)


def checkout(clone: Path, commit: str) -> None:
    run("git", "checkout", "-q", commit, cwd=clone)


# --- skill discovery and integrity -----------------------------------------------


def discover_skills(checkout_dir: Path) -> dict[str, list[Path]]:
    """Map skill name -> directories containing SKILL.md, found recursively."""
    found: dict[str, list[Path]] = {}
    for skill_md in checkout_dir.rglob("SKILL.md"):
        if ".git" in skill_md.parts:
            continue
        found.setdefault(skill_md.parent.name, []).append(skill_md.parent)
    return found


def resolve_selected(
    upstream: dict[str, list[Path]], names: Iterable[str], *, missing_ok: bool = False
) -> dict[str, Path]:
    """Name -> upstream directory; raise listing every ambiguous name, and every missing
    one unless `missing_ok` (a newly selected skill is absent from the *locked* release)."""
    problems: list[str] = []
    resolved: dict[str, Path] = {}
    for name in sorted(names):
        dirs = upstream.get(name, [])
        if not dirs:
            if not missing_ok:
                problems.append(f"missing upstream: {name}")
        elif len(dirs) > 1:
            problems.append(f"ambiguous upstream: {name} ({', '.join(map(str, dirs))})")
        else:
            resolved[name] = dirs[0]
    if problems:
        raise AutomationError(
            "selected skills could not be resolved in the release; nothing was changed\n  "
            + "\n  ".join(problems)
        )
    return resolved


_FRONTMATTER_KEY = re.compile(r"^(name|description):\s*(.*?)\s*$")
_BLOCK_SCALARS = frozenset({">", "|", ">-", "|-", ">+", "|+"})


def frontmatter_fields(skill_md: Path) -> dict[str, str]:
    """`name` and `description` from YAML frontmatter, tolerating block scalars."""
    lines = skill_md.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields: dict[str, str] = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            break
        match = _FRONTMATTER_KEY.match(line)
        if not match:
            continue
        key, value = match.groups()
        if value in _BLOCK_SCALARS:
            rest = [line.strip() for line in lines[i + 1 :] if line.startswith((" ", "\t"))]
            value = rest[0] if rest else ""
        fields[key] = value.strip("\"'")
    return fields


def validate_skill(name: str, directory: Path) -> list[str]:
    """Lightweight integrity check: one SKILL.md, name/description present, name == directory."""
    problems: list[str] = []
    if len(list(directory.rglob("SKILL.md"))) != 1:
        problems.append("expected exactly one SKILL.md")
    fields = frontmatter_fields(directory / "SKILL.md")
    if not fields.get("name"):
        problems.append("frontmatter has no name")
    elif fields["name"] != name:
        problems.append(f"frontmatter name {fields['name']!r} != directory {name!r}")
    if not fields.get("description"):
        problems.append("frontmatter has no description")
    return problems


def validate_all(selected: dict[str, Path]) -> None:
    problems = {n: validate_skill(n, d) for n, d in selected.items()}
    failing = {n: p for n, p in problems.items() if p}
    if failing:
        lines = [f"{n}: {'; '.join(p)}" for n, p in sorted(failing.items())]
        raise AutomationError(
            "release skills failed integrity checks; nothing was changed\n  " + "\n  ".join(lines)
        )
