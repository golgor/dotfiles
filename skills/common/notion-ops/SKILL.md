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

Read `~/.config/notion-axi/routes.toml` for canonical database and template IDs.
If `routes.toml` is missing, run `mise run setup-notion-routes` to restore it from Bitwarden.

The file defines table sections for each supported route:
- `[projects]`: contains `database_id`, `data_source_id`, `template_id`, `template_name`
- `[tasks]`: contains `database_id`, `data_source_id`, `template_id`, `template_name`

### Projects

Use the `database_id` and `data_source_id` under `[projects]`.
Native template: `template_id` (named by `template_name`).
Use for project records across discovery and delivery, including customer work, infrastructure, and internal tools.

### Tasks

Use the `database_id` and `data_source_id` under `[tasks]`.
Native template: `template_id` (named by `template_name`).

Link project work through **Parent project** on the task, paired with **Tasks** on the project.
Standalone tasks may have no project. Ask when the intended project is unclear.
Relations contain project page IDs, not database or template IDs.
Execution work belongs in the Tasks database, not duplicate project-page checklists.

For other Notion content, use the supplied page URL or confirm a target through search.
These two routes do not select destinations for meetings, catalogs, or standalone decision records.

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
