"""Fixtures: a local tagged git repo standing in for GitHub, and a throwaway dotfiles root."""

from pathlib import Path

import pytest

from tests.helpers import Dotfiles, Upstream, git, write_skill


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
