# skills/

Locally maintained agent skills. Edit skills in place and review changes as ordinary repo diffs. Upstream material is a starting point, not an immutable snapshot.

## Scope and selection

| directory | role | reaches |
| --- | --- | --- |
| `common/<name>/` | always-on local extras | Pi, Claude Code, Codex |
| `matt/<name>/` | selected Matt Pocock skills | Pi, Claude Code, Codex |
| `pstack/<name>/` | selected pstack skills | Pi, Claude Code, Codex |
| `claude/<name>/` | Claude-only extras | Claude Code only |

Common skills are always deployed. `mise run deploy-skills` selects exactly one of `matt/` or `pstack/`; Matt is the default for every plain invocation and bootstrap, with no remembered state. Use `mise run deploy-skills -- --stack pstack` to select pstack. Selection is a deployment choice, not a change to source files.

The deployer projects one directory symlink per selected skill into the harness discovery directories. It prunes stale managed links and repoints moved skills with the same name, while refusing conflicts and preserving foreign neighbours. Run it after adding, removing, or moving a skill; content edits are live immediately.

`common/` and the selected stack reach all three harnesses; `claude/` remains Claude-only. Deployment does not provide harness adapters, autonomy, or runtime capabilities. The existing `comment-sicko` agent remains independently installed; `pstack/no-comments` is the only adopted pstack skill here and is not an upstream import/refresh. Common is the shared dependency layer regardless of where a skill originated; `common/codebase-design` intentionally remains there because pstack/no-comments uses it.

## Authoring and adopting

Use a directory containing `SKILL.md` with frontmatter `name` matching the directory and a non-empty `description`. Keep reference files beside it. Read the `writing-for-agents` skill when changing skill instructions.

When adopting third-party material, add `SOURCE.md` in that skill directory with its upstream repository, source path, adopted commit, and license. Preserve required license and copyright notices alongside it. Keep historical source paths when moving a skill. Review upstream changes by hand; there is no upstream sync task or lock manifest.

Every file here is public. Skills must not contain machine paths, tokens, or credentials.
