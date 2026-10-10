# Notion routes

## Source of truth

Read sibling `routes.toml` at `~/.pi/agent/capsules/notion-manager/skills/notion-ops/references/routes.toml` for canonical database, data-source, native-template, and people IDs. The configuration is restored from the Notes field of the Bitwarden item `Notion`; keep actual values there, outside this reference and public dotfiles.

If the file is missing, ensure the `notion-manager` capsule is checked out, then return these setup actions to the parent:

```sh
mise bootstrap dotfiles apply
mise -C ~/.dotfiles run setup-notion-routes
```

After authorized setup, read the restored file. Verify destinations, live schemas, and template availability through `notion-axi` before drafting or applying records.

## Projects

Use `[projects]`: `database_id`, `data_source_id`, `template_id`, and `template_name`.

Route project records across discovery and delivery here, including customer work, infrastructure, and internal tools. Select the named native template explicitly; the database default is not a substitute.

## Tasks

Use `[tasks]`: `database_id`, `data_source_id`, `template_id`, and `template_name`.

Execution work belongs in the Tasks database rather than duplicate project-page checklists. Link project work through **Parent project** on the task, paired with **Tasks** on the project. Relations contain project page IDs, not database or template IDs.

Standalone tasks may have no project. Ask the parent when the intended project is unclear.

## People

Read `[people.<name>]`: `name`, `user_id`, and optional `email`. Use `user_id` for people properties such as Assignee; Notion rejects names.

If a person is missing, read their ID from a page they are assigned to and propose adding the mapping. Changes to route configuration require separate approval.

## Other destinations

For meetings, catalogs, standalone decisions, or other content, use the supplied page URL or confirm a target through search. Projects and Tasks routes do not choose those destinations.
