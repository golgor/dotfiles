"""The tracked manifest: upstream repo, selected skills per scope, locked release."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from automation import AutomationError

Scope = Literal["common", "claude"]
SCOPES: tuple[Scope, ...] = ("common", "claude")

MANIFEST = Path(".mise/skills/mattpocock.toml")
SCOPE_DIRS: dict[Scope, Path] = {scope: Path("skills") / scope for scope in SCOPES}


@dataclass(frozen=True)
class Release:
    tag: str
    commit: str  # empty until the first update run records one


@dataclass(frozen=True)
class Manifest:
    repo: str
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
_COMMIT = re.compile(r"^([0-9a-f]{40})?$")  # empty until the first update records one


def _repo(value: object) -> str:
    repo = _string(value, "repo")
    if not _REPO.match(repo):
        raise AutomationError(f"manifest: repo must look like owner/name, got {repo!r}")
    return repo


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
                raise AutomationError(f"skill selected in two scopes: {name}")
            selection[name] = scope

    release = _table(data.get("release"), "release")
    return Manifest(
        repo=_repo(data.get("repo")),
        release=Release(
            tag=_string(release.get("tag"), "release.tag"),
            commit=_commit(release.get("commit")),
        ),
        selection=selection,
    )


def record_release(path: Path, release: Release) -> None:
    """Rewrite only the tag/commit lines so hand-written comments and selection survive."""
    text = path.read_text()
    for key, value in (("tag", release.tag), ("commit", release.commit)):
        text, count = re.subn(rf'^{key} = ".*"$', f'{key} = "{value}"', text, flags=re.M)
        if count != 1:
            raise AutomationError(
                f"expected exactly one `{key} = ...` line in {path}, found {count}"
            )
    path.write_text(text)
