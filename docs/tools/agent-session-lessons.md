# Agent Session Lessons

Observations from real agent sessions, kept as candidate material for the harness system prompt. Each entry
records what happened and the rule it suggests. Nothing here is active configuration — it is a staging area
for prompt changes, reviewed and promoted by hand.

Entries earn their place by changing behaviour versus the model's default. An observation the agent already
gets right without being told belongs in the log below only long enough to be recognised as a no-op and cut.

---

## 1. A written artifact records intent, not current status

**What happened:** During a Notion planning session, research turned up a project (`BLE Processing`) whose
tasks matched the work being scoped, including one marked Done with merged code in
`ToolSense/iot-go-ble-processor`. That became a headline "this duplicates an existing project" finding and an
entire round of design questions built on top of it. The user's response: *"This is based on false
information. `iot-go-ble-processor` will most likely never be deployed."*

The evidence was real; the *status* was stale. A backlog page records what someone intended when they wrote
it, and nothing in the page announces that the plan was abandoned.

**Candidate rule:** Treat a plan, backlog item, or design doc as evidence of intent at time of writing. When
a conclusion depends on whether that intent is still live — is this project active, is this code deployed,
is this the current approach — confirm with the human before building on it. The human is the cheapest and
most reliable source for live organisational state, and the only source when the artifact does not record
its own abandonment.

---

## 2. Match investigation depth to the stage the human is at

**What happened:** Mid-session, while the goal was still separating one initiative into distinct projects,
research was dispatched into flespi's plugin internals, attach points, and cost arithmetic. The user
stopped it: *"Can we focus on the high level now? I don't want research about various topics now, I know the
details so please ask me. Research is the next level when we have a clear separation of projects/tasks."*

The research was accurate and later useful. It arrived one stage early, and the depth itself was the problem.

**Candidate rule:** Read the stage from what the human is asking for. Scoping and separation work needs
breadth and their judgement; implementation work needs depth and verified facts. When the human signals they
hold the domain knowledge, asking is faster and more accurate than researching.

---

## 3. "Find facts yourself" means environment facts

**What happened:** The `grilling` skill instructs: *"Finding facts is your job, never the user's. When a
frontier question needs a fact from the environment, dispatch a sub-agent."* Read broadly, that pushed
toward researching organisational state and domain detail the user already held — the behaviour in §2.

**Candidate rule:** The self-serve mandate covers what the environment can answer: filesystem, code, tool
output, published documentation. It does not cover live organisational state, what a team currently intends,
or knowledge the human has offered to supply. Those come from the human, and asking is not a failure to do
the work.

---

## 4. Separate "the document says X" from "your plan is wrong"

**What happened:** The user justified a sequencing decision with *"we eliminate storage in calculators"*.
The source document said the opposite for the step under discussion — *"the calculators keep computing"* — so
that was raised as a correction, with a table showing the storage pools moving independently.

The document was quoted correctly and the conclusion was still wrong: the user's plan was that this step
*enables* later calculator removal, which the document does not describe because nobody had written it down
yet. The disagreement was between a document and an intention, not between a document and an error.

**Candidate rule:** When the human's statement conflicts with a source, lead with what the source says and
ask how it squares with their plan. Reserve flat contradiction for facts the source settles outright.
Plans routinely exceed what is written down, and the human is the authority on their own intent.

---

## 5. An incidental remark is not a structural fact

**What happened:** The user mentioned in passing that Node-RED flows *"are in separate tabs, so when one
flow is moved, that tab can potentially be removed"*. That became a structural assumption in two drafted
project pages — migration unit of "one flow at a time", and "the BLE tab can be removed". Several rounds
later: *"There is only one flow in Nodered. There is however several calculators that send to this one flow."*
Both pages needed reworking, one after it was already created.

**Candidate rule:** An aside answers the question asked, not every question it appears to touch. Before an
incidental detail becomes the organising principle of an artifact, confirm it as such — especially when it
determines a unit of work, a sequence, or a boundary.

---

## 6. Check a delegate's tools before assigning the work

**What happened:** Two read-only research agents were dispatched with instructions to run a CLI. One
reported back: *"my toolset has no bash/eval capability, so I cannot run `notion-axi` at all"*, and had
fallen back to guessing from local repo files. The recovery was to run the CLI in the parent session, dump
results to `/tmp`, and hand over file paths.

**Candidate rule:** Match the assignment to the delegate's capabilities. Read-only agents receive files and
paths; command execution stays with an agent that has a shell. When delegating work that depends on a tool,
name the tool and confirm the delegate can reach it — or pre-fetch the data and pass it as files.

---

## 7. Read the schema before writing to a typed system

**What worked:** Before creating any Notion project row, the target database's select options were fetched
and the exemplar page was read for structure. Every subsequent create used valid enum values first time.
Where this was skipped — a `people` property set by display name — it failed validation and cost a round
trip.

**Candidate rule:** For a system with a typed schema, read the schema and one existing record before the
first write. Enum values, required fields, and identifier formats are cheap to look up and expensive to
guess.

---

## 8. Draft-then-approve per artifact, not per batch

**What worked:** Five project pages were drafted one at a time, each reviewed before creation. Every single
one came back with substantive corrections — a wrong cost figure, a retired approach still framed as the
plan, a missing constraint, an incorrect data flow. Batching the five would have propagated the same
misunderstandings into all of them.

**Candidate rule:** When producing several artifacts from the same understanding, get the first one approved
before drafting the rest. Corrections on the first almost always apply to the others, and the human's review
is the mechanism that surfaces them.

---

## 9. Name the cost basis when quoting numbers

**What happened:** Cost figures were carried across a long session and reused in drafts. They were derived
from object counts multiplied by a published tariff, not read from an invoice, because the available token
could not reach billing. Scope changes then invalidated some of them — removing one workstream dropped a
saving from roughly €120/mo to €60/mo, while an earlier summary still quoted the old figure.

**Candidate rule:** State the basis alongside a quantity — measured, derived, or estimated — and re-derive
it when scope changes. A number that outlives its assumptions gets quoted as fact by the next reader.

---

## Tool facts

These belong in the per-tool docs rather than the system prompt; recorded here so they are not lost.
Canonical homes: [`docs/axi/notion-axi.md`](../axi/notion-axi.md) and
[`docs/axi/slack-axi.md`](../axi/slack-axi.md).

**notion-axi**

- `page create --parent` needs the **data-source** id, not the database id. `db view <db-id>` reports the
  data-source id; passing the database id returns `object_not_found`.
- `people` properties need a user **uuid**. `users get` is `RESTRICTED_RESOURCE` for a personal token, so
  read the uuid from a page the person is already assigned to via
  `api GET /v1/pages/<id>`.
- Page bodies return as a single long line with escaped `\n`, and the output pipeline truncates long lines.
  To read a full body: run the CLI from an eval cell, replace `\\n` with real newlines, strip `<span …>`
  tags, write to a file, then read that file with line ranges.
- Inline comment threads anchored to rich text are not blocks — their ids return `object_not_found` from
  `comments list`. Page-level comments work.
- Markdown converts well: headings, nested bullets, tables and links all survive. Four-space-indented
  blocks become code blocks. Square brackets in those blocks get escaped to `\[…\]`, so prefer parentheses
  in ASCII diagrams.

**slack-axi**

- Sending is two steps by design: `draft <channel> "<text>"` then `draft send <draft-id>`. The draft
  response resolves and echoes the target channel, which is a useful confirmation before posting to a DM id.
