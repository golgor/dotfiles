"""Fixtures: a local tagged git repo standing in for GitHub, and a throwaway dotfiles root."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from automation.skills.manifest import MANIFEST

GIT_ENV = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "GIT_CONFIG_GLOBAL": "/dev/null",
}


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=GIT_ENV
    )
    return result.stdout.strip()


def write_skill(
    directory: Path, name: str, body: str = "", *, description: str = "Does things."
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n{body}"
    )


@dataclass
class Upstream:
    """A local clone-able repo with tags. `latest` selects what `latest_tag()` reports."""

    path: Path
    latest: str = ""

    def latest_tag(self) -> str:
        return self.latest

    def clone(self, dest: Path) -> None:
        git("clone", "-q", "--no-checkout", str(self.path), str(dest), cwd=self.path)

    def commit(self, message: str, tag: str | None = None) -> str:
        git("add", "-A", cwd=self.path)
        git("commit", "-q", "--allow-empty", "-m", message, cwd=self.path)
        if tag:
            git("tag", "-a", "-m", tag, tag, cwd=self.path)
            self.latest = tag
        return git("rev-parse", "HEAD", cwd=self.path)


@pytest.fixture
def upstream(tmp_path: Path) -> Upstream:
    """v1.0.0 with skills alpha (common-ish, has agents/openai.yaml) and beta, plus extra."""
    path = tmp_path / "upstream"
    path.mkdir()
    git("init", "-q", cwd=path)
    write_skill(path / "skills/engineering/alpha", "alpha", "# alpha v1\n")
    (path / "skills/engineering/alpha/agents").mkdir()
    (path / "skills/engineering/alpha/agents/openai.yaml").write_text(
        "interface:\n  display_name: alpha\n"
    )
    write_skill(path / "skills/productivity/beta", "beta", "# beta v1\n")
    write_skill(path / "skills/misc/extra", "extra", "# extra v1\n")
    repo = Upstream(path)
    repo.commit("v1.0.0", tag="v1.0.0")
    return repo


@dataclass
class Dotfiles:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / MANIFEST

    def write_manifest(
        self,
        *,
        common: list[str],
        claude: list[str] | None = None,
        tag: str = "",
        commit: str = "",
    ) -> None:
        def toml_list(items: list[str] | None) -> str:
            items = items or []
            return "[" + ", ".join(f'"{i}"' for i in items) + "]"

        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(
            "# header comment survives\n"
            'repo = "example/skills"\n\n'
            "[release]\n"
            f'tag = "{tag}"\n'
            f'commit = "{commit}"\n\n'
            "[scopes]\n"
            f"common = {toml_list(common)}\n"
            f"claude = {toml_list(claude)}\n"
        )

    def commit_all(self, message: str = "snapshot") -> None:
        git("add", "-A", cwd=self.root)
        git("commit", "-q", "--allow-empty", "-m", message, cwd=self.root)


@pytest.fixture
def dotfiles(tmp_path: Path) -> Dotfiles:
    root = tmp_path / "dotfiles"
    root.mkdir()
    git("init", "-q", cwd=root)
    (root / "mise.toml").write_text(
        '[dotfiles]\n"~/.agents/skills" = { source = "skills/common", mode = "symlink-each" }\n'
    )
    repo = Dotfiles(root)
    repo.write_manifest(common=["alpha", "beta"])
    repo.commit_all("init")
    return repo


@pytest.fixture
def applied() -> list[Path]:
    """Records roots passed to the apply hook instead of running mise."""
    return []
