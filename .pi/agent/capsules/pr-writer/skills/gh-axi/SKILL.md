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

## Publish flow

Publish only when task explicitly asks to create, update, or publish a pull request.

1. Refresh remote state before inspecting history or creating a branch.
2. Inspect `git status`; identify intended paths. Stop if unrelated changes make scope unclear.
3. Stage only intended paths. Check the cached diff and run `git diff --cached --check`.
4. Commit only after reading cached diff. Write commit message from cached diff.
5. Push branch with Git.
6. Create or update PR through `gh-axi` with reviewed title and body.
7. Read the published PR through `gh-axi`; report URL, branch, commit, and CI state.

## Boundaries

- Draft-only is default. Publishing needs explicit task approval.
- Never merge, close, reopen, delete, rebase, force-push, deploy, alter secrets, or change repository settings.
- Never claim CI passed when no CI ran or checks are pending.
- On CLI validation failure, read the CLI help and correct the invocation. Do not switch to another GitHub client.

## Source

Adapted from the operational principle in the upstream `gh-axi` skill:

<https://github.com/kunchenguid/gh-axi/blob/main/skills/gh-axi/SKILL.md>
