"""`omarchy-plugins sync`: install and enable, once, the plugins listed for this host.

Manual task, run from a logged-in desktop: enabling talks to the running omarchy-shell.
Plugins already installed are never touched again, so shell.json stays Omarchy's.
"""

import argparse
import io
import socket
import sys
from pathlib import Path
from typing import TextIO

from automation import AutomationError
from automation.omarchy_plugins.host import OmarchyHost, PluginHost
from automation.omarchy_plugins.manifest import MANIFEST, load_plugins
from automation.omarchy_plugins.plan import plan
from automation.process import git_root


def run_sync(
    root: Path,
    host_name: str,
    host: PluginHost,
    *,
    dry_run: bool = False,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> bool:
    """Return False if any install failed; every other install is still attempted."""
    planned = plan(load_plugins(root / MANIFEST), host_name, host.installed())

    for plugin in planned.present:
        print(f"present    {plugin.id}", file=out)
    for plugin_id in planned.unmanaged:
        print(f"unmanaged  {plugin_id}  {host.origin(plugin_id) or '(no git origin)'}", file=out)
    if not planned.install:
        print("Nothing to install.", file=out)
        return True

    ok = True
    for plugin in planned.install:
        if dry_run:
            print(f"would install  {plugin.id}  {plugin.git}", file=out)
            continue
        try:
            host.add(plugin)
        except AutomationError as e:
            print(f"failed     {plugin.id}: {e}", file=err)
            ok = False
        else:
            print(f"installed  {plugin.id}", file=out)
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omarchy-plugins",
        description="Manage Omarchy shell plugins from omarchy/plugins.toml.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sync = sub.add_parser(
        "sync",
        help="install and enable plugins listed for this host that are missing",
        description=(
            "Install (omarchy plugin add --enable) every plugin in omarchy/plugins.toml whose "
            "hosts include this machine and whose directory is missing. Installed plugins are "
            "left alone; installed plugins not listed for this host are reported, never removed."
        ),
    )
    sync.add_argument("--dry-run", action="store_true", help="print the plan, change nothing")
    return parser


def main(argv: list[str] | None = None) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)
    args = build_parser().parse_args(argv)
    try:
        ok = run_sync(git_root(), socket.gethostname(), OmarchyHost(), dry_run=args.dry_run)
    except (AutomationError, OSError) as e:
        print(f"omarchy-plugins {args.command}: {e}", file=sys.stderr)
        return 1
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
