# automation/

Python-implemented mise tasks for this repo: one uv project, one package (`automation`), one subpackage per automation. Root `AGENTS.md` decides *when* something belongs here (logic worth testing, vs. bash glue); this file says how the code is shaped. Run `mise run check` (ruff, format, ty, pytest — all offline) before every commit.

## Automations

| subpackage | console script | mise task | does |
| --- | --- | --- | --- |
| `skills` | `skills update [manifest]` | `update-skills` (append a manifest name to update just one) | vendors selected skills from upstream manifests in `../.mise/skills/*.toml` into `../skills/{common,claude}/`, records tag/commit, deploys skill symlinks |
| `skills` | `skills deploy` | `deploy-skills` | projects one directory symlink per skill from `../skills/{common,claude}/` into `~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills` |

### `skills` module map

| module | role | prints? |
| --- | --- | --- |
| `manifest.py` | discover and parse manifests in `.mise/skills/*.toml` into `Manifest`/`Release` (shape-validated; `repo` must be `owner/name`, `branch` a valid ref, `commit` a 40-hex SHA or empty); collision check across manifests; `record_release` rewrites only release lines so comments survive | no |
| `upstream.py` | `ReleaseSource` protocol (`GitHubUpstream` adapter supports both release tags and branch tracking); `discover_skills` (recursive by `SKILL.md`), `resolve_selected`, frontmatter integrity checks | no |
| `sync.py` | dirty-tree check, `trees_differ`, divergence check against locked release, verbatim copy, orphan detection | no |
| `update.py` | `plan()` decides and returns a `Plan`; `execute()` writes it | no |
| `deploy.py` | `deploy_skills` converges every harness discovery directory (`HARNESSES`: Pi, Claude Code, Codex) to one directory symlink per skill — creates, re-points, and prunes managed links; refuses via `AutomationError` on any other conflict | no |
| `cli.py` | argparse (`skills update [name]`, `skills deploy`), multi-manifest sequencing, and every `print` | yes |

Shared: `process.py` (`run`, `git_root`) is the **only** module that calls `subprocess`; `AutomationError` in `__init__.py` is the one exception CLIs catch and print.

## Conventions

- **Implementation must follow TDD, preferably using the `/tdd` skill.** Write failing unit or integration tests first before writing production code. Keep tests completely offline by using local git fixtures (`tests/helpers.py::Upstream` / `Dotfiles`) rather than network calls. Follow red → green → refactor, and run `mise run check` to verify formatting, strict typing (`ty`), and test suite health.
- **Library code returns findings or raises `AutomationError`; only `cli.py` prints.** Tests then assert on values, not captured stdout.
- **A seam exists where two adapters exist.** `ReleaseSource` has GitHub in production and `tests/helpers.py::Upstream` (a local tagged git repo) in tests. Filesystem and git are exercised for real via `tmp_path`; `deploy.py`'s `deploy_skills` is injected into `cli.py::run_update` as a callable (`Deploy`) and not run for real in most tests.
- **Subprocess safety lives in `process.py`.** Argv sequences, never `shell=True`. Program names and flags are literals at every call site; the data-derived values (`repo`, `commit`, release tag) are validated in `manifest.py` or passed in option-proof form (`refs/tags/<tag>`, after `--`). The `# nosemgrep` markers record that the audit rule was checked — keep them accurate if you add a subprocess call, and add it in `process.py`.
- **Typing is strict: ty with every rule as an error, over `src` and `tests`.** Narrow `Any` at the boundary (see `manifest.py::_string/_table`) instead of annotating it away. No `type: ignore`, no `cast`.
- **Runtime is stdlib-only; dev tools are the `dev` group.** Tasks call `uv run --no-dev`, which works offline on a fresh machine because uv builds `uv_build` projects natively — as long as the `uv_build` range in `pyproject.toml` contains the uv version pinned in `../mise.toml`. Bump both together. Adding a runtime dependency is a `CONTEXT.md` decision, not a `pyproject.toml` edit.
- **Vendored skills are immutable.** The updater refuses to overwrite a `skills/common/<name>` that differs from the locked release; nothing in this package should ever edit skill contents.

## Adding an automation

1. Write the failing test first (follow TDD, preferably using the `/tdd` skill): fixtures in `tests/conftest.py`, helpers in `tests/helpers.py`.
2. Create `src/automation/<name>/` with `cli.py` exposing `main(argv) -> int` that catches `AutomationError`.
3. Add `<name> = "automation.<name>.cli:main"` under `[project.scripts]` in `pyproject.toml`.
4. Add `[tasks.<name>]` in `../mise.toml` running `uv run --project automation --no-dev <name> …`, and describe it in the table above.
5. `mise run check` green; run the task once for real.

## Verifying `skills update` for real

`mise run update-skills` from the repo root must print `Already at <tag/sha>; nothing to do.` when all manifests are current. To exercise the refusal path, append a line to a vendored `SKILL.md`, commit it, run the task (expect `differs from locked`), then `git reset --hard HEAD~1`. Commit only that scratch change — `git commit -a` will sweep in unrelated work.

## Verifying `deploy-skills` for real

Run `mise run deploy-skills` twice; the second run must report every link already up to date. Confirm the deployed entries are symlinks, not directories: `ls -la ~/.codex/skills`. A real directory there is the old `symlink-each` shape, which Codex silently ignores — that shape is the entire reason this module exists. Confirm discovery for real: `codex exec "list every skill you have available whose name contains tdd"` must name `tdd`.
