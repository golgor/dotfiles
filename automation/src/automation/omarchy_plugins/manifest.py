"""The tracked plugin list: git source and target hosts per plugin."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from automation import AutomationError

MANIFEST = Path("omarchy/plugins.toml")

# git reaches omarchy-plugin-add argv, id names a plugin dir; both rule out option-like values.
_ID = re.compile(r"^[A-Za-z0-9][\w.-]*$")
_GIT = re.compile(r"^(https://|git@)\S+$")
_KEYS = {"id", "git", "hosts"}


@dataclass(frozen=True)
class Plugin:
    id: str
    git: str
    hosts: tuple[str, ...]  # empty = every host

    def for_host(self, host: str) -> bool:
        return not self.hosts or host in self.hosts


def _string(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise AutomationError(f"plugins manifest: {where} must be a string")
    return value


def _plugin(entry: object, index: int) -> Plugin:
    where = f"plugin #{index}"
    if not isinstance(entry, dict):
        raise AutomationError(f"plugins manifest: {where} must be a table")
    unknown = sorted(str(k) for k in entry if k not in _KEYS)
    if unknown:
        raise AutomationError(f"plugins manifest: unknown key in {where}: {', '.join(unknown)}")

    plugin_id = _string(entry.get("id"), f"{where}.id")
    if not _ID.match(plugin_id):
        raise AutomationError(
            f"plugins manifest: {where}.id must be a plugin id, got {plugin_id!r}"
        )
    where = plugin_id
    git = _string(entry.get("git"), f"{where}.git")
    if not _GIT.match(git):
        raise AutomationError(f"plugins manifest: {where}.git must be an https:// or git@ URL")
    hosts = entry.get("hosts", [])
    if not isinstance(hosts, list):
        raise AutomationError(f"plugins manifest: {where}.hosts must be a list of hostnames")
    return Plugin(
        id=plugin_id,
        git=git,
        hosts=tuple(_string(h, f"{where}.hosts") for h in hosts),
    )


def load_plugins(path: Path) -> list[Plugin]:
    if not path.is_file():
        raise AutomationError(f"missing manifest: {path}")
    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise AutomationError(f"invalid manifest {path}: {e}") from e
    entries = data.get("plugin", [])
    if not isinstance(entries, list):
        raise AutomationError("plugins manifest: use [[plugin]] entries")

    plugins = [_plugin(entry, i) for i, entry in enumerate(entries, start=1)]
    seen: set[str] = set()
    for plugin in plugins:
        if plugin.id in seen:
            raise AutomationError(f"plugins manifest: plugin listed twice: {plugin.id}")
        seen.add(plugin.id)
    return plugins
