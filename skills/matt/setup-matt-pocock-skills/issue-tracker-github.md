# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use `gh-axi` for every GitHub operation; it routes through authenticated `gh` and returns compact TOON output by default. Use `gh-axi api` when an operation is not covered by a resource command. Read live help before relying on a flag, and use `--fields` or API `--jq` only where supported.

## Conventions

- **Create an issue**: `gh-axi issue create --title "..." --body "..."`. Use `--body-file` for multi-line bodies.
- **Read an issue**: `gh-axi issue view <number> --comments` (add `--full` when complete bodies are needed).
- **List issues**: `gh-axi issue list --state open` with appropriate `--label` and `--assignee` filters. The default output includes issue identity and title; use only supported optional fields from live help (for example, `body`, `closedAt`, `labels`, `milestone`, `updatedAt`, and `url`). Output is TOON; for a precise machine-readable projection use `gh-axi api ... --jq ...`.
- **Make an issue a sub-issue of a parent**: create the child, then `gh-axi issue subissue add <parent> <child>`. List links with `gh-axi issue subissue list <parent>`. If sub-issues are unavailable, put `Part of #<parent>` at the top of the child body.
- **Comment on an issue**: `gh-axi issue comment <number> --body "..."` (or `--body-file`).
- **Apply / remove labels**: `gh-axi issue edit <number> --add-label "..."` / `--remove-label "..."`.
- **Close**: `gh-axi issue close <number> --comment "..."`.

Infer the repo from `git remote -v`; `gh-axi` does this automatically when run inside a clone. Resource commands return compact TOON by default: `gh-axi api` prints an `api_response` wrapper whose `body` is an escaped TOON scalar, including when `--jq` is used. Unwrap that `body` before piping to `jq`, `sed`, or other parsers. Read live help before relying on a flag; do not assume resource commands accept arbitrary `--json`/`--jq` flags.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the `gh-axi pr` equivalents:

- **Read a PR**: `gh-axi pr view <number> --comments` and `gh-axi pr diff <number>`.
- **List external PRs for triage**: `gh-axi pr list --state open` (the default output includes identity and title; use only optional fields supported by live help, such as `body`, `createdAt`, `labels`, `mergedAt`, `milestone`, `updatedAt`, and `url`). Determine whether a PR is external from GitHub's API `author_association` value, not from the displayed author name; use `gh-axi api --paginate ... --jq ...` for that projection, then retain only authors whose association is outside the repository's maintainer/collaborator policy.
- **Comment / label / close**: `gh-axi pr comment`, `gh-axi pr edit --add-label`/`--remove-label`, `gh-axi pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh-axi pr view 42` and fall back to `gh-axi issue view 42`.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `gh-axi issue create --label wayfinder:map`.
- **Child ticket**: create an issue and link it with `gh-axi issue subissue add <map> <child>`. Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies** are the canonical, UI-visible representation. Add an edge with `gh-axi api POST /repos/{owner}/{repo}/issues/<child>/dependencies/blocked_by --field issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's full numeric **database id**, obtained with `gh-axi api /repos/{owner}/{repo}/issues/<n> --jq .id` (not the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only, the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: first list the map's explicitly linked sub-issues with `gh-axi issue subissue list <map>` (or the map's task-list entries when native sub-issues are unavailable); do not substitute a global open-issue listing. For each listed child, inspect its state, assignee, and native dependency summary, then keep open, unassigned children with no open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line). The first eligible child in map order wins. Use `gh-axi api --paginate ... --jq ...` for exact dependency projections.
- **Claim**: `gh-axi issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh-axi issue comment <n> --body "<answer>"`, then `gh-axi issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.
