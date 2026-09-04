"""The tracked manifest: upstream repo, selected skills per scope, locked release."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from automation import AutomationError

Scope = Literal["common", "claude"]
SCOPES: tuple[Scope, ...] = ("common", "claude")

MANIFESTS_DIR = Path(".mise/skills")
SCOPE_DIRS: dict[Scope, Path] = {scope: Path("skills") / scope for scope in SCOPES}


@dataclass(frozen=True)
class Release:
    commit: str  # 40-hex SHA; empty until the first update run records one
    tag: str = ""  # release/tag name if tracking tags/releases; empty if tracking branches

    def label(self) -> str:
        if self.tag:
            return f"release {self.tag} ({self.commit[:12]})"
        return f"commit {self.commit[:12]}" if self.commit else "unrecorded"


@dataclass(frozen=True)
class Manifest:
    name: str  # stem of filename, e.g. "mattpocock" or "toolsense"
    path: Path  # path to the manifest toml file
    repo: str  # "owner/name"
    branch: (
        str | None
    )  # branch name if tracking a branch (e.g. "main"), None if tracking releases/tags
    release: Release
    selection: dict[str, Scope]

    def dest(self, root: Path, name: str) -> Path:
        return root / SCOPE_DIRS[self.selection[name]] / name

    def names(self) -> list[str]:
        return sorted(self.selection)


def as_scope(value: str) -> Scope:
    for scope in SCOPES:
        if value == scope:
            return scope
    raise AutomationError(f"unknown scope in manifest: {value}")


# tomllib returns Any; these narrow it into the shape we expect, with readable errors.


def _string(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise AutomationError(f"manifest: {where} must be a string")
    return value


def _strings(value: object, where: str) -> list[str]:
    if not isinstance(value, list):
        raise AutomationError(f"manifest: {where} must be a list of strings")
    return [_string(v, where) for v in value]


def _table(value: object, where: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AutomationError(f"manifest: [{where}] table is missing")
    return {_string(k, where): v for k, v in value.items()}


# repo and release.commit are the two manifest values that reach git/gh argv; both are
# constrained to shapes that cannot be mistaken for options.
_REPO = re.compile(r"^[\w.-]+/[\w.-]+$")
_BRANCH = re.compile(r"^[A-Za-z0-9_][\w.-]*(?:/[A-Za-z0-9_][\w.-]*)*$")
_COMMIT = re.compile(r"^([0-9a-f]{40})?$")  # empty until the first update records one


def _repo(value: object) -> str:
    repo = _string(value, "repo")
    if not _REPO.match(repo):
        raise AutomationError(f"manifest: repo must look like owner/name, got {repo!r}")
    return repo


def _branch(value: object) -> str | None:
    if value is None:
        return None
    branch = _string(value, "branch")
    if not _BRANCH.match(branch):
        raise AutomationError(f"manifest: branch must be a valid ref name, got {branch!r}")
    return branch


def _commit(value: object) -> str:
    commit = _string(value, "release.commit")
    if not _COMMIT.match(commit):
        raise AutomationError(f"manifest: release.commit must be a full 40-hex SHA, got {commit!r}")
    return commit


def load_manifest(path: Path) -> Manifest:
    if not path.is_file():
        raise AutomationError(f"missing manifest: {path}")
    try:
        data = _table(tomllib.loads(path.read_text()), "manifest")
    except tomllib.TOMLDecodeError as e:
        raise AutomationError(f"invalid manifest {path}: {e}") from e

    selection: dict[str, Scope] = {}
    for key, names in _table(data.get("scopes"), "scopes").items():
        scope = as_scope(key)
        for name in _strings(names, f"scopes.{key}"):
            if name in selection:
                raise AutomationError(f"skill selected in two scopes in {path.name}: {name}")
            selection[name] = scope

    release = _table(data.get("release"), "release")
    tag_val = release.get("tag")
    tag = _string(tag_val, "release.tag") if tag_val is not None else ""
    return Manifest(
        name=path.stem,
        path=path,
        repo=_repo(data.get("repo")),
        branch=_branch(data.get("branch")),
        release=Release(
            commit=_commit(release.get("commit")),
            tag=tag,
        ),
        selection=selection,
    )


def discover_manifests(root: Path) -> list[Manifest]:
    manifests_dir = root / MANIFESTS_DIR
    if not manifests_dir.is_dir():
        raise AutomationError(f"missing manifests directory: {manifests_dir}")
    paths = sorted(manifests_dir.glob("*.toml"))
    if not paths:
        raise AutomationError(f"no manifests found in {manifests_dir}")
    manifests = [load_manifest(p) for p in paths]
    check_collisions(manifests)
    return manifests


def check_collisions(manifests: list[Manifest]) -> None:
    seen: dict[tuple[Scope, str], str] = {}
    collisions: list[str] = []
    for m in manifests:
        for name, scope in m.selection.items():
            key = (scope, name)
            if key in seen:
                prev = seen[key]
                msg = (
                    f"skill {name!r} in scope {scope!r} is claimed by both {prev!r} and {m.name!r}"
                )
                collisions.append(msg)
            else:
                seen[key] = m.name
    if collisions:
        raise AutomationError("manifest collision detected:\n  " + "\n  ".join(collisions))


def record_release(path: Path, release: Release) -> None:
    """Rewrite only the tag/commit lines so hand-written comments and selection survive."""
    text = path.read_text()
    if release.tag:
        text, count = re.subn(r'^tag = ".*"$', f'tag = "{release.tag}"', text, flags=re.M)
        if count != 1:
            raise AutomationError(f"expected exactly one `tag = ...` line in {path}, found {count}")
    text, count = re.subn(r'^commit = ".*"$', f'commit = "{release.commit}"', text, flags=re.M)
    if count != 1:
        raise AutomationError(f"expected exactly one `commit = ...` line in {path}, found {count}")
    path.write_text(text)
