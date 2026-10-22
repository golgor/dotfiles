---
name: setup-pstack
description: Configure portable Pi model choices for pstack roles. Detects available models, adjusts supported thinking levels, and writes a confirmed role map. Use for /setup-pstack, "configure pstack models", or "pstack budget".
---

## Harness integration note
Read [`../PSTACK-HARNESS.md`](../PSTACK-HARNESS.md) before applying this workflow.

# Setup pstack

Configure `~/.agents/pstack-models.md`, a portable role map for native Pi subagents. Missing role entries inherit the parent model; do not apply Cursor or upstream defaults.

## Steps

### 1. Detect available models

Run `pi --list-models`. Use the listed `provider/id` values as the available base models. If none can be detected, ask the user to provide them. Do not guess model IDs or write an unconfirmed choice.

### 2. Load current state

If `~/.agents/pstack-models.md` exists, read its role lines and budget line. Otherwise begin with every role inheriting the parent model. Ignore and report labels not present in the role list below; do not silently convert them into a role.

### 3. Choose and confirm

Ask which budget to use and explain that it adjusts only the optional `:thinking` suffix, never the base model ID or global configuration. Offer only thinking levels supported by Pi and the selected model. If there is no existing rule, describe the initial state as `inherit-parent` for every role.

Show all role labels and current choices. For each configured value, display the base `provider/id` separately from its optional `:thinking` suffix. Validate the base ID against `pi --list-models`; validate the suffix separately against Pi's allowed thinking levels and that model's support. If the requested level is unsupported, ask for a supported level or leave the role inheriting. Do not rewrite a provider or model family to approximate a budget.

Offer the detected models and `inherit-parent` for each role. `inherit-parent` means omit the native child `model` field. `auto` may also be recorded as an alias for omission, but do not describe it as a model. Confirm every proposed change before writing. For panel roles, accept a comma-separated list of values; each entry is one native subagent, and a panel may claim model diversity only when its base IDs are distinct available models. Do not fabricate diversity when the available choices share one model.

The role labels are exact and portable:

- `feature, refactoring`
- `bug-fix`
- `perf-issue`
- `hillclimb`
- `judgment and prose`
- `hardest tasks`
- `how explorer`
- `how explainer`
- `why investigators`
- `why synthesizer`
- `reflect tooling`
- `reflect judgment, divergent, synthesizer`
- `arena runners`
- `arena cross-judge pool`
- `swarm workers`
- `architect runners`
- `interrogate reviewers`

### 4. Write the confirmed rule

Only after confirmation, write `~/.agents/pstack-models.md`. Use exactly one `role: value` line per configured role. Values are `inherit-parent` or exact `provider/id[:thinking]`; panel roles use comma-separated values. Omitting a role line also means inheritance. Preserve base model IDs unchanged when adjusting thinking levels. Example format (illustrative values only; check inventory and thinking support before using):

```text
# pstack model choices for native Pi subagents; unlisted roles inherit the parent model.
# budget: medium
feature, refactoring: inherit-parent
bug-fix: provider/model-id:high
how explorer: provider/model-id:medium
arena runners: provider/model-id:high, other-provider/other-model:medium
```

Do not run setup generators, write a rule during installation, change global settings, mise tools, or installed providers.

### 5. Offer optional generators

After writing the confirmed rule, check whether the project already has a `verify-*` skill or an existing harness. If not, offer once to invoke `/create-verification-skill`. Also check for formal verification coverage and offer `/create-formal-verification-skill` only if none exists. These are optional and require the user's choice.
