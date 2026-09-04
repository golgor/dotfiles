"""Test helpers: git plumbing, skill writers, and the two repos every test needs."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from automation.skills.manifest import MANIFESTS_DIR, Release

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
    """A local clone-able repo with tags or branches."""

    path: Path
    latest: str = ""
    branch: str | None = None

    def label(self) -> str:
        if self.branch:
            return f"branch {self.branch}"
        return f"release {self.latest}"

    def resolve_latest(self, clone: Path) -> Release:
        if self.branch:
            commit = git("rev-parse", f"origin/{self.branch}^{{commit}}", cwd=clone)
            return Release(commit=commit, tag="")
        commit = git("rev-parse", f"refs/tags/{self.latest}^{{commit}}", cwd=clone)
        return Release(commit=commit, tag=self.latest)

    def clone(self, dest: Path) -> None:
        git("clone", "-q", "--no-checkout", str(self.path), str(dest), cwd=self.path)

    def commit(self, message: str, tag: str | None = None, branch: str | None = None) -> str:
        git("add", "-A", cwd=self.path)
        git("commit", "-q", "--allow-empty", "-m", message, cwd=self.path)
        if branch:
            git("branch", "-M", branch, cwd=self.path)
            self.branch = branch
        if tag:
            git("tag", "-a", "-m", tag, tag, cwd=self.path)
            self.latest = tag
        return git("rev-parse", "HEAD", cwd=self.path)


@dataclass
class Dotfiles:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / MANIFESTS_DIR / "example.toml"

    def manifest_path(self, name: str = "example") -> Path:
        return self.root / MANIFESTS_DIR / f"{name}.toml"

    def write_manifest(
        self,
        name: str = "example",
        *,
        repo: str = "example/skills",
        branch: str | None = None,
        common: list[str] | None = None,
        claude: list[str] | None = None,
        tag: str = "",
        commit: str = "",
    ) -> Path:
        def toml_list(items: list[str] | None) -> str:
            items = items or []
            return "[" + ", ".join(f'"{i}"' for i in items) + "]"

        path = self.manifest_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        branch_line = f'branch = "{branch}"\n' if branch else ""
        tag_line = f'tag = "{tag}"\n' if tag else ('tag = ""\n' if not branch else "")
        path.write_text(
            "# header comment survives\n"
            f'repo = "{repo}"\n'
            f"{branch_line}\n"
            "[release]\n"
            f"{tag_line}"
            f'commit = "{commit}"\n\n'
            "[scopes]\n"
            f"common = {toml_list(common)}\n"
            f"claude = {toml_list(claude)}\n"
        )
        return path

    def commit_all(self, message: str = "snapshot") -> None:
        git("add", "-A", cwd=self.root)
        git("commit", "-q", "--allow-empty", "-m", message, cwd=self.root)
