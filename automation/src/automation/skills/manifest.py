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


def load_manifest(path: Path) -> Manifest:
    if not path.is_file():
        raise AutomationError(f"missing manifest: {path}")
    data = _table(tomllib.loads(path.read_text()), "manifest")

    selection: dict[str, Scope] = {}
    for key, names in _table(data.get("scopes"), "scopes").items():
        scope = as_scope(key)
        for name in _strings(names, f"scopes.{key}"):
            if name in selection:
                raise AutomationError(f"skill selected in two scopes: {name}")
            selection[name] = scope

    release = _table(data.get("release"), "release")
    return Manifest(
        repo=_string(data.get("repo"), "repo"),
        release=Release(
            tag=_string(release.get("tag"), "release.tag"),
            commit=_string(release.get("commit"), "release.commit"),
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
