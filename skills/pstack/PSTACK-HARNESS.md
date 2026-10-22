# pstack on Pi

This adapter is the Pi contract for the pstack skills imported beside this file. The source is upstream pstack commit `9b93e81fb2921b9263d9463c15bafeabfe3903aa`; imported skill files remain the source workflow policy. Read this harness first, then read the requested sibling `SKILL.md` in full. Relative upstream documentation is mapped to `docs/pstack/UPSTREAM.md` and `docs/pstack/guide/`; source agents are `.pi/agent/agents/`.

## Invocation

- Use `/skill:name` for a literal Pi skill invocation (for example `/skill:how`, `/skill:why`, `/skill:tdd`, or `/skill:poteto-mode`). Pi appends the remainder as the request.
- A bare `/name` in pstack prose is a logical helper invocation: read the sibling `skills/pstack/name/SKILL.md` and apply it. It is not a Pi slash tool unless Pi's command menu explicitly exposes it.
- `/poteto-mode` is the front door and owns its playbook, todo list, and every delegate. Do not use `poteto-agent` to run the playbook itself.

## Native delegation contract

Delegation is permitted only when the operator's request or applicable instructions grants it and the current Pi session has the native `subagent` tool. Use the installed `pi-subagents` API, never an inline imitation or a CLI fallback:

```text
subagent({
  "agent": "poteto-agent" | "pstack-reader" | "scout" | "reviewer" | "worker",
  "task": "<bounded task; include absolute sibling skill paths and required evidence>",
  "cwd": "<required target repository>",
  "async": true | false,
  "options": { "context": "fresh" | "fork" },
  "model": "<exact provider/id:thinking>" // omit to inherit parent
})
```

`agent` is the `subagent_type` equivalent. Use the local `pstack-reader` profile for general-purpose read-only inspection or challenge: it inherits project/global context and skills, has only `read` and `bash`, and has no model pin. Do not assume the built-in `scout` or `reviewer` inherit those contexts. `poteto-agent`/`worker` are writer lanes only when their actual tools permit edits. Map a general-purpose write task to `poteto-agent` only when explicitly delegated. Preserve requested readonly intent and do not widen tools. `async: true` launches in the background; native completion notifications wake the parent. Inspect with `subagent({action:"status", id})` only when needed. Native workflows return completion notifications; do not use `bg_wait`. A failed launch is a failed lane: report its exact error and do not silently retry inline, with `pi -ne`, or through another CLI.

Tasks must name absolute sibling paths, for example `/absolute/project/skills/pstack/how/SKILL.md` and `/absolute/project/skills/pstack/poteto-mode/SKILL.md`. Say whether the child is fresh or forked, and what project/global context it must inherit. Fresh is the default for workers; use `context: "fork"` only when the parent transcript is intentionally required. Use a profile whose actual inheritance fields supply the needed context; task wording cannot enable profile inheritance. Context inheritance supplies instructions, not action authority: tools, nesting ceilings, and operator grants still govern.

Nested calls require an actual child-safe `subagent` tool, permitted depth, and the operator's grant. A coordinator must also have `subagent_supervisor` to answer descendants. Without those, the child must use native `contact_supervisor` with the exact absolute skill/task path and wait for the parent; it must not inline a sketch, guess, or bypass the ceiling.

## Models and panels

Default is `inherit-parent`: omit `model` unless the operator selected a model. Read portable role choices from `~/.agents/pstack-models.md`; never guess Cursor slugs or write Cursor config. `pi --list-models` is the discovery command for base `provider/id` values. An optional `:thinking` suffix is a Pi reasoning level, not part of the model ID; validate the base ID against the inventory and the suffix separately against Pi's allowed levels and model support. Budget edits change only confirmed role choices, not global mise tools. A panel may claim model diversity only when each listed base ID is a distinct available Pi model; never fake diversity by relabeling one model.

`/setup-pstack` is advisory in Pi: after operator confirmation, translate its choices into the portable `~/.agents/pstack-models.md` format. Do not write that file during installation or without confirmation. `inherit-parent` and `auto` mean omission of the child `model` field, not model names.

## Workflows and support boundaries

The useful Pi path is `/skill:poteto-mode` plus `/skill:how`, `/skill:why`, `/skill:tdd`, and `/skill:poteto-help`, with native `subagent` calls for delegated work and native async lifecycle for background work. GitHub access uses `gh-axi`; when explicitly requested, PR publication uses the local publication-only `pr-writer` profile. Do not wait for CI unless the caller asks to babysit it. Transcripts and evidence are scoped to the current Pi session/workspace; never glob `~/.cursor` across projects. AXI/provider/tool mappings come from the installed Pi environment and available extensions, not Cursor MCP names.

The following are not silently emulated: Cursor custom modes, `/loop`, cloud agents, Automations, cursor-team-kit, Origin, Cursor MCP, or Cursor's native sandbox semantics. Report a prerequisite or skip the step. Native Pi worktrees are isolation, not a sandbox. Upstream scripts requiring Bun or cloud services may remain copied as source, but are not run automatically. Unsupported shipping/autopilot behavior must be reported rather than claimed complete.

Pi-specific mappings replace upstream Task, model, and path directives. The remaining source workflow policy stays authoritative, subject to higher operator instructions. This file translates invocation, delegation, model, context, and lifecycle semantics to Pi.
