---
name: notion-ops
description: Route Notion projects and tasks, use their native templates, and verify approved writes via notion-axi. Load for Notion reads, searches, page edits, project/task creation, or publishing.
---

# Notion Ops

Use `notion-axi`. Run it without arguments for connection status and next commands.

For `notion-axi api`, use `/v1/...` paths. The shorter paths in its help returned `invalid_request_url` on 2026-09-14.
Use `--content-file`, `--append-file`, or `--replace-file` for multiline bodies. Literal `\n` text previously broke block formatting.
Check rendering conventions against the current command documentation and the rendered page.

## Routes

Before resolving any record destination, template, or assignee, read [Notion routes](references/routes.md). That reference owns routing rules and the lookup/setup path for private configuration.

## Read and draft

1. Resolve the target. Before creating a record, check the intended database for an existing match.
2. Fetch the live schema with `notion-axi db view <database-id>`.
   For relation targets and allowed values, use `notion-axi api /v1/data_sources/<data-source-id>`.
3. For new records, list templates with `notion-axi api /v1/data_sources/<data-source-id>/templates`.
   Read the selected template with `notion-axi page view <template-id> --full` before drafting.
   If its ID is missing or its purpose changed, ask rather than choosing another silently.
4. Fill the native template with confirmed context. Remove guidance and empty placeholders from the draft.
   Keep relevant sections, decision rationale, acceptance criteria, and source links. Ask about material gaps instead of adding filler.
5. Keep owners, dates, status, and priority in database properties. Use the body for explanation, evidence, and blockers.
   Live schema overrides property instructions embedded in a template. Preserve unknown optional values instead of inventing them.

Templates stay in Notion. Select the named template explicitly for creation rather than assuming the database default matches.
Inspect current command/API support for native template application. If unavailable, report the limitation and a manual plan.
For existing pages, read the full body and preserve unrelated content. Template structure is not permission to replace an existing page.

## Approve, apply, verify

1. Show the target, proposed properties, body changes, relations, and template choice. Obtain explicit approval before any Notion write.
2. Apply only the approved changes. Template edits and database/view changes need their own approved scope.
3. Read back the page. Verify the body, properties, and project relation, and report its URL plus any unverified result.

Verify effects, not acknowledgments:
- A linked task view once reported success without retaining its relation filter. Read the filter back and confirm it selects the intended project. Report manual follow-up if it cannot be verified.
- A template-created page can initially have an empty body. Confirm that template application finished before writing content into it.
- If a write times out, inspect the target before retrying. The template update timed out on 2026-09-14, but read-back matched the approved body.

For auth failures, stop and report the error with a manual plan. After two failed write attempts, stop and ask.
Keep routing independent of provider-specific tool names.
