# automation/

Python-implemented mise tasks for this repo: one uv project, one package (`automation`), one subpackage per automation. Root `AGENTS.md` decides *when* something belongs here (logic worth testing, vs. bash glue); this file says how the code is shaped. Run `mise run check` (ruff, format, ty, pytest — all offline) before every commit.

## Automations

| subpackage | console script | mise task | does |
| --- | --- | --- | --- |
| `skills` | `skills deploy` | `deploy-skills` | projects common plus the selected `../skills/{matt,pstack}/` stack, and Claude-only skills, as one directory symlink per skill into `~/.agents/skills`, `~/.claude/skills`, `~/.codex/skills` |
| `omarchy_plugins` | `omarchy-plugins sync [--dry-run]` | `sync-omarchy-plugins` | installs and enables missing plugins from `../omarchy/plugins.toml` for this host |

### `omarchy_plugins` module map

| module | role | prints? |
| --- | --- | --- |
| `manifest.py` | parses and validates `../omarchy/plugins.toml` into plugin IDs, git URLs and optional hosts | no |
| `plan.py` | plans install/present/unmanaged states from the manifest and installed plugin directories | no |
| `host.py` | `PluginHost` protocol and Omarchy adapter for plugin add/enable commands | no |
| `cli.py` | `omarchy-plugins sync [--dry-run]`; executes the plan and reports outcomes | yes |

### `skills` module map

| module | role | prints? |
| --- | --- | --- |
| `deploy.py` | `deploy_skills` converges every harness discovery directory (`HARNESSES`: Pi, Claude Code, Codex) to one directory symlink per skill — creates, re-points, and prunes managed links; refuses via `AutomationError` on any other conflict | no |
| `cli.py` | argparse (`skills deploy`), repository validation, and deployment reporting | yes |

Shared: `process.py` (`run`, `git_root`) is the **only** module that calls `subprocess`; `AutomationError` in `__init__.py` is the one exception CLIs catch and print.

## Conventions

- **Implementation must follow TDD, preferably using the `/tdd` skill.** Write failing unit or integration tests first before writing production code. Keep tests offline with temporary directories and local git repositories rather than network calls. Follow red → green → refactor, and run `mise run check` to verify formatting, strict typing (`ty`), and test suite health.
- **Library code returns findings or raises `AutomationError`; only `cli.py` prints.** Tests then assert on values, not captured stdout.
- **Exercise filesystem and git for real in temporary directories.** Deployment tests call `deploy_skills(root, home)` with a temporary home so tests leave live harness discovery directories untouched.
- **Subprocess safety lives in `process.py`.** Argv sequences, never `shell=True`. Program names and flags are literals at every call site; pass data-derived arguments in option-proof form (`--flag=value` or after `--`) where the command supports it. The `# nosemgrep` markers record that the audit rule was checked — keep them accurate if you add a subprocess call, and add it in `process.py`.
- **Typing is strict: ty with every rule as an error, over `src` and `tests`.** Narrow `Any` at the boundary instead of annotating it away. No `type: ignore`, no `cast`.
- **Runtime is stdlib-only; dev tools are the `dev` group.** Tasks call `uv run --no-dev`, which works offline on a fresh machine because uv builds `uv_build` projects natively — as long as the `uv_build` range in `pyproject.toml` contains the uv version pinned in `../mise.toml`. Bump both together. Adding a runtime dependency is a `CONTEXT.md` decision, not a `pyproject.toml` edit.
- **Deployment is content-blind.** It links skill directories without reading or rewriting their contents. Skill authoring and provenance rules belong in `../skills/AGENTS.md`.

## Adding an automation

1. Write the failing test first (follow TDD, preferably using the `/tdd` skill): shared helpers in `tests/helpers.py`, fixtures beside their tests.
2. Create `src/automation/<name>/` with `cli.py` exposing `main(argv) -> int` that catches `AutomationError`.
3. Add `<name> = "automation.<name>.cli:main"` under `[project.scripts]` in `pyproject.toml`.
4. Add `[tasks.<name>]` in `../mise.toml` running `uv run --project automation --no-dev <name> …`, and describe it in the table above.
5. `mise run check` green; run the task once for real.

## Verifying `deploy-skills` for real

Run `mise run deploy-skills` twice; the second run must report every link already up to date. Confirm the deployed entries are symlinks, not directories: `ls -la ~/.codex/skills`. A real directory there is the old `symlink-each` shape, which Codex silently ignores — that shape is the entire reason this module exists. Confirm discovery for real: `codex exec "list every skill you have available whose name contains tdd"` must name `tdd`.

## Verifying `sync-omarchy-plugins` for real

Run `mise run sync-omarchy-plugins --dry-run` to review missing and already-present plugins, then `mise run sync-omarchy-plugins` to install and enable missing plugins. A second dry-run must report `Nothing to install.`
