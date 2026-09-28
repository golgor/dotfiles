"""The PluginHost seam: what is installed, where it came from, and installing one plugin."""

from pathlib import Path
from typing import Protocol

from automation import AutomationError
from automation.omarchy_plugins.manifest import Plugin
from automation.process import run

PLUGINS_DIR = Path.home() / ".config/omarchy/plugins"


class PluginHost(Protocol):
    def installed(self) -> set[str]: ...

    def origin(self, plugin_id: str) -> str | None: ...

    def add(self, plugin: Plugin) -> None: ...


class OmarchyHost:
    """Omarchy discovers plugins by directory; enabling goes through the running shell."""

    def __init__(self, plugins_dir: Path = PLUGINS_DIR) -> None:
        self.plugins_dir = plugins_dir

    def installed(self) -> set[str]:
        if not self.plugins_dir.is_dir():
            return set()
        return {
            p.name
            for p in self.plugins_dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")  # skip omarchy's .add.tmp.* clones
        }

    def origin(self, plugin_id: str) -> str | None:
        plugin_dir = self.plugins_dir / plugin_id
        if not (plugin_dir / ".git").exists():  # never let git walk up into a parent repo
            return None
        try:
            return run("git", "remote", "get-url", "origin", cwd=plugin_dir)
        except AutomationError:
            return None

    def add(self, plugin: Plugin) -> None:
        # --enable reuses omarchy's wait-for-discovery loop; --yes skips its prompts.
        run("omarchy-plugin-add", plugin.git, "--enable", "--yes")
        if not (self.plugins_dir / plugin.id).is_dir():
            raise AutomationError(
                f"cloned {plugin.git} but no {plugin.id}/ appeared; "
                "the id in plugins.toml must match the plugin's manifest.json id"
            )
