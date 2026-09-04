"""Test helpers: git plumbing, skill writers, and the two repos every test needs."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

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
