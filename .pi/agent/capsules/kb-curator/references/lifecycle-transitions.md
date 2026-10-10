# Lifecycle transitions

Use this procedure for approved note moves and their associated status changes. It supplements the pinned `memory-lifecycle` skill; that skill's separate move and metadata calls are not a transaction.

## Prepare

Read the note and applicable KB/schema contract. Confirm the approved destination and exact metadata changes. A folder change alone does not authorize an invented status or completion date.

Before the first mutation, save a transition record in the configured report artifact:

- resolved project;
- original note identity, path, permalink, and affected metadata/status observations;
- approved destination and metadata/status changes;
- current phase: `planned`;
- verification results and remaining work.

Proceed when the record exists and every intended mutation matches the approved scope. If the report cannot be saved, return blocked without moving the note.

## Move and verify

Call `move_note` once. Read back the destination using the identity returned by the tool or its approved path; verify path and permalink behavior against the project settings. Update the transition record to `moved` with actual identity/path/permalink.

If the call fails or its result is ambiguous, inspect original and destination states before taking another action. Continue only when one verified note is at the approved destination. Otherwise record the partial state and escalate; do not guess which copy to edit or delete.

## Apply metadata and verify

Using the verified destination identity, apply only the approved metadata/status changes with `edit_note`. Preserve unrelated fields and content.

Read back the note and confirm the destination, approved metadata/status observations, permalink behavior, and applicable schema checks. Mark the transition `complete` only when all applicable checks pass. A successful move alone is `moved`, not `complete`.

## Recover a partial transition

If metadata editing fails after a verified move, read the destination again:

- Intended metadata already present: verify the remaining checks; do not repeat the edit.
- Intended metadata missing and current affected fields still match the recorded original state: retry that approved metadata edit once, then read back and verify.
- Unexpected state, unresolved identity, failed retry, or interrupted run: keep phase `moved` or `blocked` and report exact actual state plus remaining approved work to the parent.

On a resumed run, require the saved transition record and matching approval scope. Read actual state before completing the missing step. If either is unavailable, return a recovery proposal for approval. Never repeat a completed move merely because the original run stopped.

Rollback is a separate approved operation. Preserve partial state rather than automatically moving the note back or deleting anything. This procedure supports detection and bounded recovery, not atomicity or protection against concurrent external writers.
