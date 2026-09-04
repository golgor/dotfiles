# skills/

The one tracked copy of the agent skills deployed to Pi, Codex, and Claude Code. Root `AGENTS.md` has the ownership model; this file is what to check before touching anything in here.

## Is this skill vendored?

Look it up in the manifests under `../.mise/skills/*.toml`. If the name is in a `scopes` list in any manifest, the directory is a **verbatim, immutable snapshot** of the recorded upstream release or branch commit. Do not edit it, not even a typo: `mise run update-skills` compares every vendored directory against its locked commit and refuses to run while one differs, so a local edit blocks all future updates. The `writing-for-agents` skill applies to skills you author, never to vendored ones.

To change a vendored skill, fork it: copy the directory to a new name that is not in any manifest, edit the copy, and leave the original. A directory in `common/` or `claude/` whose name is not in any manifest is yours; the updater ignores it.

To add, drop, or move a vendored skill, edit the manifest's `scopes` lists and run `mise run update-skills`. It syncs the selection, reports upstream skills you have not selected, and warns about directories a dropped or moved name leaves behind — delete those by hand.

To add a new upstream source, create a new manifest file `../.mise/skills/<source>.toml` with `repo`, optional `branch = "..."` (if tracking a branch instead of release tags), `[release]`, and `[scopes]`. Then run `mise run update-skills`. The updater enforces that no two manifests claim the same skill name.

## Scope is the directory

| directory | reaches | deployment |
| --- | --- | --- |
| `common/<name>/` | Pi (`~/.agents/skills`), Claude Code (`~/.claude/skills`), Codex (`~/.codex/skills`) | automatic: `mise run deploy-skills` (`skills deploy`) |
| `claude/<name>/` | Claude Code only | automatic: `mise run deploy-skills` (`skills deploy`) |

There is no `pi/` or `codex/` scope directory: Codex sees everything in `common/`, just through its own discovery directory (`~/.codex/skills`) rather than `~/.agents/skills`, so a separate scope would only produce duplicate-name warnings.

## Authoring a skill of your own

Follow the Agent Skills format the updater validates for vendored ones: a `<name>/SKILL.md` whose frontmatter `name` equals the directory and has a non-empty `description`; sidecars (`agents/openai.yaml`, reference files) sit beside it. After creating or removing a skill directory, run `mise run deploy-skills` — the *set* of skills changed, so the symlinks must be re-projected. Content edits inside an existing skill are live immediately.

Every file here is public. Skills must not carry machine paths, tokens, or anything from a harness's runtime state.
