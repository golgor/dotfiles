# skills/

Locally maintained agent skills. Edit skills in place and review changes as ordinary repo diffs. Upstream material is a starting point, not an immutable snapshot.

## Scope and deployment

| directory | reaches |
| --- | --- |
| `common/<name>/` | Pi, Claude Code, Codex |
| `claude/<name>/` | Claude Code only |

`mise run deploy-skills` projects one directory symlink per skill into the harness discovery directories. Run it after adding, removing, or moving a skill. Content edits are live immediately. Root `AGENTS.md` explains why directory symlinks are required and which neighbours belong to other tools.

Deployment is content-blind: it links every directory in a scope without reading `SKILL.md`. `disable-model-invocation: true` affects discovery in harnesses that support it, not deployment.

## Authoring and adopting

Use a directory containing `SKILL.md` with frontmatter `name` matching the directory and a non-empty `description`. Keep reference files beside it. Read the `writing-for-agents` skill when changing skill instructions.

When adopting third-party material, add `SOURCE.md` in that skill directory with its upstream repository, source path, adopted commit, and license. Preserve required license and copyright notices alongside it. Keep this provenance when adapting the skill. Review upstream changes by hand; there is no upstream sync task or lock manifest.

Every file here is public. Skills must not contain machine paths, tokens, or credentials.
