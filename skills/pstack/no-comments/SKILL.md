---
name: no-comments
description: "Spawn Comment Sicko, fix accepted findings, and offer encodings for claimed constraints."
disable-model-invocation: true
---

# No comments

Spawn Comment Sicko. Act on accepted findings.

Defer to Comment Sicko's fresh perspective.

## Scope

Use the caller's files or diff. Otherwise use the current diff against the base branch, default `main`, including the working tree. Resolve that scope to concrete files and diff hunks before spawning. Preserve pre-existing edits; if a report is rejected, revert only changes from that run.

## Pi adapter

Requires Pi's `pi-subagents` extension and the registered `comment-sicko` agent. If either is unavailable, stop and report the missing prerequisite.

The upstream helper skills are not installed here. Translate their names as follows:

- `/how`: trace the named symbol, callers, and tests in nearby code.
- `/why`: inspect git history and linked issues or specifications for the constraint. Refresh remote state before relying on it. Distinguish evidence from guesses.
- `/architect`: read the local **codebase-design** skill and sketch the smallest in-scope redesign. Stop at the sketch.
- **principle-fix-root-causes** and **principle-redesign-from-first-principles**: intent to remove the cause, not add symptom guards or widen scope.

Pass the `/how` and `/why` translations with the scope in the child's task so its unchanged upstream prompt can use them. These are harness adapters, not additional deletion rules.

## Steps

1. Call Pi's `subagent` tool with `agent: "comment-sicko"`, the scope and helper translations as `task`, the target repository as `cwd`, and `options: { context: "fresh" }`. Inherit the session model and use the agent's configured reasoning level. Do not restate its rules. Wait for its completion before inspecting or editing the same scope.
2. Inspect its report and diff. Reject application-code edits, scope escapes, exception-protected deletions, misstated `MUST KILL` reasons, and flags that treat kept intentional code as guilty. Reshape flags on our-code surprises stay actionable. Do not restore those comments. A keep survives only with proof it is about something we cannot change. Audit missed scoped lint and TypeScript suppressions. Correctness or safety suppressions stay actionable `MUST KILL`s. Restore deletions only with exact exceptions and scoped proof. Before accepting thin `IMPORTANT` or `do not remove` kills or keeps, run `/how` or `/why` on their symbol. If a kill is ambiguous, do not restore. If a keep is refuted or still ambiguous, delete it. Revert and rerun one rejected report with the failure named. Reject a second, report it open, and fail `/no-comments`.
3. Fix trivial accepted flags directly by deleting a dead path, dropping a parameter, or using the real API. If any fix needs a shape, run `/architect` once for the accepted set and surrounding code. Stop at the sketch. Architect shapes. Step 4 implements.
4. Implement the smallest root-cause fix in scope. Remove every named workaround. If the root cause is out of scope, land the smallest in-scope fix and report the rest open. The **principle-fix-root-causes** and **principle-redesign-from-first-principles** skills guide intent only. Neither authorizes widening the fence nor fixing instances outside it. Never bolt on symptom guards.
5. Constraint comments say `do not remove`, `do not change wording`, or `talk to X before changing`. Leave keeps about things we cannot change. Offer the cheapest in-scope type, runtime, test, or CI lint. Wait for interactive approval. Unattended and eval require caller pre-approval. If approved, encode then delete. Otherwise delete, report the constraint open, and sketch out-of-scope work.
6. Report the deletion count, restored comments, reruns, architect sketch, fixes, encoding offers, encodings, unenforced constraints, and other open work.
