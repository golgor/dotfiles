"""The skills deployment CLI and its reports."""

import argparse
import io
from pathlib import Path

import pytest

from automation.skills.cli import build_parser, print_deployment
from automation.skills.deploy import Deployment


def test_parser_accepts_deploy_and_rejects_update() -> None:
    assert build_parser().parse_args(["deploy"]).command == "deploy"
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["update"])
    assert exc.value.code == 2


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
