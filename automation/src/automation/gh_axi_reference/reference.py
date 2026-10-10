"""Collect and render the installed gh-axi documented command help."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from automation import AutomationError
from automation.process import run

OUTPUT = Path(".pi/agent/capsules/pr-writer/skills/gh-axi/references/commands.md")
CommandRunner = Callable[..., str]
_VERSION = re.compile(r"\A\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?\Z")
_USAGE = re.compile(r"\Ausage:\s+gh-axi\s+")
_SECTION = re.compile(r"(?m)^([a-z][a-z0-9-]*)\[(\d+)\]:\s*$")
_COMMAND_NAME = re.compile(r"\A[a-z][a-z0-9-]*\Z")


@dataclass(frozen=True)
class Snapshot:
    """Validated output from one version and help discovery pass."""

    version: str
    root_help: str
    groups: tuple[tuple[str, str], ...]


def _clean(output: str, description: str) -> str:
    value = output.replace("\r\n", "\n").strip()
    if not value:
        raise AutomationError(f"empty {description}")
    return value


def _version(output: str) -> str:
    value = _clean(output, "gh-axi version")
    if "\n" in value or not _VERSION.fullmatch(value):
        raise AutomationError(f"malformed gh-axi version: {value!r}")
    return value


def parse_root_groups(output: str) -> tuple[str, ...]:
    """Extract command groups from root help, rather than maintaining a list."""
    value = _clean(output, "root help")
    lines = value.splitlines()
    if not lines or not _USAGE.match(lines[0]):
        raise AutomationError("malformed root help: missing usage")

    commands = next((m for m in _SECTION.finditer(value) if m.group(1) == "commands"), None)
    if commands is None:
        raise AutomationError("malformed root help: missing commands section")
    flags = next(
        (m for m in _SECTION.finditer(value, commands.end()) if m.group(1) == "flags"), None
    )
    if flags is None:
        raise AutomationError("malformed root help: missing flags section")

    expected = int(commands.group(2))
    names: list[str] = []
    root_only: set[str] = set()
    for line in value[commands.end() : flags.start()].splitlines():
        entry = line.strip()
        if not entry:
            continue
        match = re.fullmatch(r"(\([^)]*\)|[a-z][a-z0-9-]*)=(.+)", entry)
        if match is None:
            raise AutomationError(f"malformed root help command entry: {entry!r}")
        for name in match.group(2).split(","):
            name = name.strip()
            if not _COMMAND_NAME.fullmatch(name):
                raise AutomationError(f"malformed root help command name: {name!r}")
            names.append(name)
            if match.group(1) == "(none)" and not root_only:
                root_only.add(name)

    if len(names) != expected or len(set(names)) != len(names) or not names:
        raise AutomationError("malformed root help: command count does not match entries")
    groups = sorted(set(names) - root_only)
    if not groups:
        raise AutomationError("malformed root help: no group commands discovered")
    return tuple(groups)


def _validate_group(group: str, output: str) -> str:
    value = _clean(output, f"help for group {group}")
    lines = value.splitlines()
    if len(lines) < 2 or not re.match(rf"\Ausage:\s+gh-axi\s+{re.escape(group)}(?:\s|$)", lines[0]):
        raise AutomationError(f"malformed help for group {group}")
    return value


def _default_runner(*args: str) -> str:
    return run(*args)


def gather(runner: CommandRunner = _default_runner) -> Snapshot:
    """Run version/root/group help, failing before any output path is touched."""
    version = _version(runner("gh-axi", "--version"))
    root_help = _clean(runner("gh-axi", "--help"), "root help")
    groups = parse_root_groups(root_help)
    details = tuple(
        (group, _validate_group(group, runner("gh-axi", group, "--help"))) for group in groups
    )
    return Snapshot(version=version, root_help=root_help, groups=details)


def render(snapshot: Snapshot) -> str:
    """Render stable Markdown with raw documented help in progressive disclosure."""
    sections = [
        "# gh-axi command reference",
        "",
        "> Generated from installed `gh-axi` version and help output.",
        "> Documented help, not an exhaustive machine-readable schema.",
        f"> Version: `{snapshot.version}`",
        "",
        "## Root help",
        "",
        "Command: `gh-axi --help`",
        "",
        "```text",
        snapshot.root_help,
        "```",
    ]
    for group, help_text in snapshot.groups:
        sections.extend(
            [
                "",
                f"## {group}",
                "",
                f"Command: `gh-axi {group} --help`",
                "",
                "```text",
                help_text,
                "```",
            ]
        )
    return "\n".join(sections) + "\n"


def refresh(root: Path, runner: CommandRunner = _default_runner) -> Path:
    """Gather all help first, then replace the generated reference once."""
    snapshot = gather(runner)
    output = root / OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(snapshot), encoding="utf-8")
    return output
