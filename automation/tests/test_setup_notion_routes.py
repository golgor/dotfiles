"""Offline integration tests for the Bitwarden-backed Notion route restore task."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / ".mise/tasks/setup-notion-routes"
DESTINATION = Path(".pi/agent/capsules/notion-manager/skills/notion-ops/references/routes.toml")
TMP_PATTERN = "routes.toml.tmp.*"


VALID_ROUTES = """[projects]
database_id = "project-db"
data_source_id = "project-source"
template_id = "project-template"

[tasks]
database_id = "task-db"
data_source_id = "task-source"
template_id = "task-template"
"""


def make_fixture(
    tmp_path: Path, content: str, *, deployed: bool = True
) -> tuple[Path, Path, dict[str, str]]:
    checkout = tmp_path / "checkout"
    references = checkout / DESTINATION.parent
    references.mkdir(parents=True)
    (references / "routes.md").write_text("# routes\n")
    (references / "routes.toml").write_text("old deployed routes\n")

    home = tmp_path / "home"
    capsule_link = home / ".pi/agent/capsules/notion-manager"
    capsule_link.parent.mkdir(parents=True)
    if deployed:
        capsule_link.symlink_to(checkout / ".pi/agent/capsules/notion-manager")

    old_local = home / ".config/notion-axi/routes.toml"
    old_local.parent.mkdir(parents=True)
    old_local.write_text("old local routes\n")

    mock_bin = tmp_path / "mock-bin"
    mock_bin.mkdir()
    rbw = mock_bin / "rbw"
    rbw.write_text(
        "#!/bin/sh\n"
        'printf \'%s\\n\' "$*" >> "$RBW_LOG"\n'
        'case "$1" in\n'
        "  unlock) exit 0 ;;\n"
        '  get) cat "$RBW_CONTENT" ;;\n'
        "esac\n"
    )
    rbw.chmod(0o755)
    content_file = tmp_path / "routes-from-rbw.toml"
    content_file.write_text(content)
    env = os.environ.copy()
    env.update(
        HOME=str(home),
        PATH=f"{mock_bin}:{env['PATH']}",
        RBW_CONTENT=str(content_file),
        RBW_LOG=str(tmp_path / "rbw.log"),
    )
    return checkout, home, env


def run_task(home: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def test_success_installs_into_deployed_capsule_checkout_with_private_mode(tmp_path: Path) -> None:
    checkout, home, env = make_fixture(tmp_path, VALID_ROUTES)

    result = run_task(home, env)

    destination = checkout / DESTINATION
    assert result.returncode == 0, result.stderr
    assert destination.read_text() == VALID_ROUTES
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert not list(destination.parent.glob(TMP_PATTERN))
    assert (home / ".config/notion-axi/routes.toml").read_text() == "old local routes\n"
    assert (tmp_path / "rbw.log").read_text().splitlines() == [
        "unlock",
        "get Notion --field notes",
    ]


@pytest.mark.parametrize(
    ("content", "error"),
    [
        ("[projects\n", "not valid TOML"),
        (
            (
                "[projects]\n"
                'database_id = "project-db"\n'
                'data_source_id = "project-source"\n'
                'template_id = "project-template"\n'
                "\n[tasks]\n"
                'database_id = "task-db"\n'
                'data_source_id = "task-source"\n'
                'template_id = "   "\n'
            ),
            "missing or has empty required key 'template_id'",
        ),
        ("", "notes field in Bitwarden item 'Notion' is empty"),
    ],
)
def test_invalid_or_empty_restore_preserves_destination_and_cleans_temp(
    tmp_path: Path, content: str, error: str
) -> None:
    checkout, home, env = make_fixture(tmp_path, content)
    destination = checkout / DESTINATION

    result = run_task(home, env)

    assert result.returncode != 0
    assert error in result.stderr
    assert destination.read_text() == "old deployed routes\n"
    assert not list(destination.parent.glob(TMP_PATTERN))


def test_missing_deployed_directory_fails_before_bitwarden(tmp_path: Path) -> None:
    _, home, env = make_fixture(tmp_path, VALID_ROUTES, deployed=False)

    result = run_task(home, env)

    assert result.returncode != 0
    assert "notion-manager capsule" in result.stderr
    assert "mise bootstrap dotfiles apply" in result.stderr
    assert not (tmp_path / "rbw.log").exists()


def test_help_shows_new_destination_without_invoking_bitwarden(tmp_path: Path) -> None:
    _, home, env = make_fixture(tmp_path, VALID_ROUTES, deployed=False)

    result = run_task(home, env, "--help")

    assert result.returncode == 0
    destination_text = ".pi/agent/capsules/notion-manager/skills/notion-ops/references/routes.toml"
    assert destination_text in result.stdout
    assert ".config/notion-axi/routes.toml" not in result.stdout
    assert not (tmp_path / "rbw.log").exists()


def test_gitignore_ignores_private_restore_and_temp_but_not_routes_reference(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitignore").write_text((ROOT / ".gitignore").read_text())
    references = repo / DESTINATION.parent
    references.mkdir(parents=True)
    (references / "routes.toml").write_text("private\n")
    (references / "routes.toml.tmp.abc123").write_text("private temp\n")
    (references / "routes.md").write_text("# routes\n")

    def ignored(path: Path) -> bool:
        relative = path.relative_to(repo)
        return (
            subprocess.run(
                ["git", "check-ignore", "--quiet", "--no-index", str(relative)],
                cwd=repo,
            ).returncode
            == 0
        )

    assert ignored(references / "routes.toml")
    assert ignored(references / "routes.toml.tmp.abc123")
    assert not ignored(references / "routes.md")
