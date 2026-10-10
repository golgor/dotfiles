"""Tests for the offline gh-axi documented-help reference refresh."""

from pathlib import Path

import pytest

from automation import AutomationError
from automation.gh_axi_reference.reference import OUTPUT, gather, parse_root_groups, refresh, render

ROOT_HELP = """usage: gh-axi [command] [args] [flags]
commands[3]:
  (none)=dashboard, zeta, alpha
flags[1]:
  --help
"""
GROUP_HELP = {
    "alpha": "usage: gh-axi alpha <subcommand> [flags]\nsubcommands[1]:\n  list\n",
    "zeta": "usage: gh-axi zeta [flags]\nexamples:\n  gh-axi zeta\n",
}


def test_root_help_discovers_and_sorts_groups() -> None:
    assert parse_root_groups(ROOT_HELP) == ("alpha", "zeta")


def test_gather_uses_only_safe_help_invocations() -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: str) -> str:
        calls.append(args)
        if args == ("gh-axi", "--version"):
            return "0.1.37\n"
        if args == ("gh-axi", "--help"):
            return ROOT_HELP
        assert len(args) == 3 and args[0] == "gh-axi" and args[2] == "--help"
        return GROUP_HELP[args[1]]

    snapshot = gather(fake_run)

    assert calls == [
        ("gh-axi", "--version"),
        ("gh-axi", "--help"),
        ("gh-axi", "alpha", "--help"),
        ("gh-axi", "zeta", "--help"),
    ]
    assert snapshot.version == "0.1.37"


def test_render_contains_metadata_and_deterministic_sections() -> None:
    def fake_run(*args: str) -> str:
        if args == ("gh-axi", "--version"):
            return "0.1.37"
        if args == ("gh-axi", "--help"):
            return ROOT_HELP
        return GROUP_HELP[args[1]]

    output = render(gather(fake_run))

    assert output.startswith("# gh-axi command reference\n")
    assert "Documented help, not an exhaustive machine-readable schema." in output
    assert "Version: `0.1.37`" in output
    assert output.index("## alpha") < output.index("## zeta")
    assert "gh-axi alpha --help" in output
    assert "\n".join(output.splitlines()[:8]).find("timestamp") == -1


def test_failed_help_does_not_rewrite_previous_reference(tmp_path: Path) -> None:
    output = tmp_path / OUTPUT
    output.parent.mkdir(parents=True)
    output.write_text("previous\n")

    def failed_run(*args: str) -> str:
        if args == ("gh-axi", "--version"):
            return "0.1.37"
        raise AutomationError("help failed")

    with pytest.raises(AutomationError, match="help failed"):
        refresh(tmp_path, failed_run)

    assert output.read_text() == "previous\n"


@pytest.mark.parametrize("bad_root", ["", "not help", "usage: gh-axi\ncommands[1]:\n  broken\n"])
def test_malformed_root_help_fails(bad_root: str) -> None:
    def fake_run(*args: str) -> str:
        if args == ("gh-axi", "--version"):
            return "0.1.37"
        return bad_root

    with pytest.raises(AutomationError, match="root help"):
        gather(fake_run)


def test_empty_or_malformed_group_help_fails() -> None:
    def fake_run(*args: str) -> str:
        if args == ("gh-axi", "--version"):
            return "0.1.37"
        if args == ("gh-axi", "--help"):
            return (
                "usage: gh-axi [command] [args] [flags]\n"
                "commands[2]:\n  (none)=dashboard, alpha\nflags[1]:\n  --help\n"
            )
        return "usage: other\n"

    with pytest.raises(AutomationError, match="help for group alpha"):
        gather(fake_run)


def test_malformed_group_help_does_not_rewrite_previous_reference(tmp_path: Path) -> None:
    output = tmp_path / OUTPUT
    output.parent.mkdir(parents=True)
    output.write_text("previous\\n")

    def fake_run(*args: str) -> str:
        if args == ("gh-axi", "--version"):
            return "0.1.37"
        if args == ("gh-axi", "--help"):
            return ROOT_HELP
        return ""

    with pytest.raises(AutomationError, match="help for group alpha"):
        refresh(tmp_path, fake_run)

    assert output.read_text() == "previous\\n"


def test_malformed_version_fails() -> None:
    with pytest.raises(AutomationError, match="version"):
        gather(lambda *_: "")
