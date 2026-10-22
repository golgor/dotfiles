"""The skills deployment CLI and its reports."""

import argparse
import io
import os
import subprocess
from pathlib import Path

import pytest

from automation.skills.cli import build_parser, print_deployment
from automation.skills.deploy import Deployment


def test_parser_accepts_deploy_and_stack_choices() -> None:
    parser = build_parser()
    args = parser.parse_args(["deploy"])
    assert args.command == "deploy"
    assert args.stack == "matt"
    assert parser.parse_args(["deploy", "--stack", "pstack"]).stack == "pstack"
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["deploy", "--stack", "other"])
    assert exc.value.code == 2


def test_parser_rejects_update() -> None:
    assert build_parser().parse_args(["deploy"]).command == "deploy"
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["update"])
    assert exc.value.code == 2


def test_cli_stack_selection_is_persistent_only_for_one_invocation(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    home = tmp_path / "home"
    root.mkdir()
    (root / "skills/common/alpha").mkdir(parents=True)
    (root / "skills/matt/teach").mkdir(parents=True)
    (root / "skills/pstack/how").mkdir(parents=True)
    (root / "mise.toml").write_text("[tasks]\n")
    subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
    environment = os.environ | {
        "HOME": str(home),
        "PYTHONPATH": str(Path(__file__).parents[1] / "src"),
    }

    pstack = subprocess.run(
        ["python", "-m", "automation.skills.cli", "deploy", "--stack", "pstack"],
        cwd=root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Deploying pstack skill stack." in pstack.stdout
    assert (home / ".agents/skills/how").is_symlink()

    matt = subprocess.run(
        ["python", "-m", "automation.skills.cli", "deploy"],
        cwd=root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Deploying matt skill stack." in matt.stdout
    assert (home / ".agents/skills/teach").is_symlink()
    assert not (home / ".agents/skills/how").exists()


def test_deploy_help_describes_the_actual_recognition_check() -> None:
    deploy_help = None
    for action in build_parser()._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparser = action.choices["deploy"]
            assert isinstance(subparser, argparse.ArgumentParser)
            deploy_help = subparser.description
    assert deploy_help is not None
    assert "symlink pointing into skills/" in deploy_help


def test_print_deployment_says_nothing_to_do_when_all_empty() -> None:
    out = io.StringIO()
    print_deployment(Deployment(linked=[], pruned=[], unchanged=[]), out)
    assert "nothing to do" in out.getvalue().lower()


def test_print_deployment_omits_zero_count_line(tmp_path: Path) -> None:
    out = io.StringIO()
    print_deployment(Deployment(linked=[tmp_path / "linked"], pruned=[], unchanged=[]), out)
    assert "0 link(s)" not in out.getvalue()
    assert "link(s) already up to date" not in out.getvalue()


def test_print_deployment_prints_nonzero_unchanged_count(tmp_path: Path) -> None:
    out = io.StringIO()
    print_deployment(Deployment(linked=[], pruned=[], unchanged=[tmp_path / "a"]), out)
    assert "1 link(s) already up to date." in out.getvalue()
