---
name: gh-axi
description: Operate GitHub through installed gh-axi. Use CLI help as source of truth for current commands and flags.
user-invocable: false
---

# gh-axi for PR writer

## Rule

Use `gh-axi` for every GitHub operation. Never substitute raw `gh`, browser automation, or direct GitHub API calls.

The installed CLI is the source of truth. Do not copy command flags from memory or this skill:

```bash
gh-axi
gh-axi --help
gh-axi <command> --help
```

## Task contract

The caller supplies `repo`, `mode`, and optional `paths`, `base`, or `pr`. These are task fields, not native subagent arguments. Discover changed files from Git; the caller need not enumerate them.

| Mode | Input and completion |
| --- | --- |
| `draft` (default) | Inspect requested changes and return PR body. Git and GitHub remain unchanged. |
| `local` | Create PR from local changes: already-staged files, unstaged tracked edits, and untracked files within requested scope. Inspect index and working tree separately; isolate intended changes on a branch, stage, verify cached diff, commit, push, and create PR. |
| `branch` | Create PR from committed branch. Use base-to-head diff; leave working-tree changes untouched. Push branch and create PR. |
| `update` | Update identified existing PR. Use complete PR base-to-head diff for its body. Commit local changes only when explicitly included in task; otherwise leave them untouched. Push authorized commits and update PR. |

Publish modes require an explicit user request to create or update a PR. A mode supplied by the caller does not grant authority beyond that request. If an open PR already exists in a create mode, report it instead of creating a duplicate. Ask only when target or intended scope cannot be determined from task and live state.

## Execution

1. Refresh remote state; inspect branch, status, and live PR metadata. Resolve base from task or repository default.
2. Establish scope from mode and optional paths. In `local`, include already-staged changes within scope. Preserve unrelated index and working-tree changes. For partially staged files, inspect both diffs; include only authorized hunks. Stop if unrelated staged changes cannot be safely separated from the intended commit.
3. For authorized local commits, stage intended changes, read cached diff, run `git diff --cached --check`, and derive commit message from cached diff. Recheck branch before committing.
4. Draft body from the complete intended PR diff using the `visual-pr` template and `show-me` visual guidance. Record available validation evidence separately in the operational handoff.
5. For publish modes, push with Git and create/update through `gh-axi`. For `draft`, return body without mutation.
6. Read back published title, body, base, head, and checks. Complete only when publication matches intended scope; report pending or absent CI accurately.

Return operational bookkeeping separately from PR body: URL, branch, commit, checks, and any excluded local changes needed for handoff.

## Boundaries

- Draft-only is default. Publishing needs explicit task approval.
- Never merge, close, reopen, delete, rebase, force-push, deploy, alter secrets, or change repository settings.
- Never claim CI passed when no CI ran or checks are pending.
- On CLI validation failure, read the CLI help and correct the invocation. Do not switch to another GitHub client.

## Source

Adapted from the operational principle in the upstream `gh-axi` skill:

<https://github.com/kunchenguid/gh-axi/blob/main/skills/gh-axi/SKILL.md>
