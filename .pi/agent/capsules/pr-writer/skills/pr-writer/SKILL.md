---
name: pr-writer
description: Draft a concise, evidence-backed PR body from a verified change. Select only structural views that help a reviewer understand the change.
---

# PR writer

## Goal

Produce one PR body that lets a reviewer answer four questions fast:

1. Why does this change exist?
2. What changed in the system?
3. What evidence says it works?
4. What can go wrong on merge or rollback?

## Gather evidence

Read before writing:

1. Current branch, status, commits, and complete diff.
2. Enough surrounding code to understand ownership and behavior.
3. Ticket, task, plan, or decision record when available.
4. Validation output that actually ran.

Use `gh-axi` only for read-only PR metadata when a current PR exists. Never publish or change Git state.

If evidence is absent, write `Not run` or `Not available`. Never infer success from changed code.

## Write this template

```markdown
## Why the change

<Exactly one sentence: problem and resulting capability.>

## Special things to note

- <1–3 reviewer-relevant risks, migrations, compatibility constraints, deliberate omissions, or surprising decisions.>
- <Use `- None.` when no note exists.>

## Change outline

<Use only smallest structural views needed.>

## Evidence

- **Before:** <failing test, previous output, or screenshot; otherwise `Not available`>
- **After:** <passing test, new output, or screenshot; otherwise `Not run`>

## Merge danger

- **Door:** <one-way | two-way>
- **Blast radius:** <specific consumers, systems, or `Low and local`>
- **Rollback:** <exact rollback path, or `Not established`>
```

## Change outline views

Use zero, one, or two views. Do not create a file-by-file changelog.

| When reviewer needs | Show |
|---|---|
| Changed behavior | Short pseudocode or control-flow diff |
| Ownership boundaries | Shallow file tree |
| API, SQL, or data shape | Contract/type fragment |
| Component/state boundary | Component tree |
| Cross-service flow | Small Mermaid sequence or flow |
| Existing shape changed | Focused `diff` block |

Put each view beside one short sentence that explains it. Show only names, calls, files, states, and boundaries needed for review.

## Quality check

Before returning:

- Use repository terms from `GLOSSARY.md` or its map when present.
- Use short neutral prose.
- Keep `Why the change` to one sentence.
- Do not repeat diff details in prose and structural view.
- Distinguish observed evidence from assumptions.
- Make unknowns visible in Evidence or Special things to note.
- State merge danger as an operational fact, not generic reassurance.

## Sources

This private skill synthesizes local `pr` and `plain-prose` guidance with selected concepts from HumanLayer's MIT-licensed `visual-pr` and `show-me` skills:

- `https://github.com/humanlayer/skills/tree/main/plugins/visual-pr`
- `https://github.com/humanlayer/skills/tree/main/plugins/show-me`

See `../../THIRD_PARTY_NOTICES.md` for license notice.
