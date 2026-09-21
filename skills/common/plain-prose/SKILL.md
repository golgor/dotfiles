---
name: plain-prose
description: Plain prose for human readers — short words, direct sentences, no fluff. Use when writing or editing a documentation page, tutorial, README, ADR, spec, PR body, release notes, or error message. Not for code, identifiers, or command syntax.
---

Words, sentences, and paragraphs. Everything above the paragraph belongs to the repo: page type, headings, frontmatter, markdown mechanics, which template to start from. Follow the repo's own standards there and do not restate them here.

## Pick the register

| Register | Applies to | Reads as |
| --- | --- | --- |
| **Warm** | Concept pages, tutorials, how-to guides, capability docs | Address the reader as "you". One analogy per new concept. Say why something matters when the reason is not obvious. |
| **Neutral** | Service pages, ADRs, reference pages, README, PR body, release notes | State the facts. Use "you" for instructions, third person otherwise. No analogies. |
| **Strict** | Runbook steps, error messages | One action per sentence, imperative. 20 words for an instruction, 25 for a description. Condition first: "If the pod is pending, check the node pool." |

Ask which register applies when the page type is ambiguous.

The register sets the tone. The word, sentence, and fluff rules below hold in all three. Warm means plain and friendly, not enthusiastic: replace a hype adjective with the fact behind it, or cut it.

## Words

Reach for the short common word.

| Write | Instead of |
| --- | --- |
| use | utilize, leverage |
| help | facilitate, enable |
| before / after | prior to, subsequent to |
| about | regarding, concerning, with respect to |
| get | obtain, acquire |
| show | demonstrate, illustrate |
| also | additionally, furthermore, moreover |
| start | begin, commence, initiate |
| make sure | ensure |
| enough | sufficient |
| analyze the log | perform an analysis of the log |

Use one name for one thing, and the same name on every page. Prefer the concrete noun: "the pod restarts" carries more than "instability occurs". Spell out a term the first time, then use it unchanged.

## Sentences

Name the actor and reach the verb early: "the parser reads the file".

Vary the length. Three sentences in a row past ~25 words: break one. Five short ones in a row: join two. Uniform sentence length is the strongest signal that nobody read the paragraph back.

Put the condition before the command.

Semicolons: write two sentences. Em dash: at most one per paragraph, for a genuine aside. A period or a colon usually does the job.

## Cut the fluff

A sentence earns its place by changing what the reader knows or does.

- Open on the first real claim. No scene-setting ("In today's cloud-native world...").
- First sentence after a heading says the next thing, never restates the heading.
- End on the last real point. Drop the closing paragraph that summarizes the page.
- State the thing directly, with no run-up ("It is important to note that", "It is worth mentioning", "This section explains").
- Say what you know: "this improves throughput", not "this may potentially help to improve throughput".
- Keep the one adjective that carries the meaning and drop its two companions.
- Name what something is, rather than what it is not ("not just X, it's Y").
- Write the content instead of announcing it ("Below, we will look at...").

## Hollow paragraphs

"The service is configured according to best practices" passes every rule above and tells the reader nothing. That gap is a missing fact, not a wording problem. Flag it the way the repo does, such as a warning admonition naming what is unverified, rather than smoothing it into clean prose.

## Before returning text

1. Any sentence that changes neither what the reader knows nor what they do: delete it.
2. Read the sentence lengths across each paragraph. Uniform: break or join.
3. Check the opener, the first sentence under each heading, and the closer against the fluff list.
