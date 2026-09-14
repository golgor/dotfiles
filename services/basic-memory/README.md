# Basic Memory stack

MCP server over `KB/`, giving agents hybrid text + vector search, categorised
observations, and a typed relation graph across the knowledge base.

```sh
cd ~/.dotfiles/services/basic-memory
docker compose up -d
docker compose exec basic-memory basic-memory status --wait
```

MCP endpoint: `http://127.0.0.1:8000/mcp`. Wired globally into `~/.config/mcp/mcp.json`
via dotfiles.

## Layout

| File | Holds |
|---|---|
| `compose.yaml` | container, mounts, transport. No settings. |
| `config.json` | every Basic Memory setting. Mounted read-write, because the server rewrites it — expect it to gain the full default set on first start. |
| `bmignore` | what is excluded from indexing, gitignore syntax. Mounted read-only; the image only creates it when absent. |

## Projects

| Project | Path | Why |
|---|---|---|
| `toolsense-kb` (default) | `KB/` | The knowledge base. Whole default search scope. |
| `toolsense-research` | `KB/20_research/` | Research *about* tooling. Out of default scope, so it stops matching every query; reachable with `project: "toolsense-research"` or `search_all_projects: true`. |

Relations must stay inside one project. A relation that crosses a project
boundary resolves as a read-time lookup in one direction only and is never
materialised as a graph edge (`relation.to_id` stays null), so `build_context`
cannot traverse it. That is why `10_sources/` stayed in `toolsense-kb` — it
carries 16 inbound `sourced_from` edges.

## Things that cost time to learn

- **Link form matters.** A filename stem does not resolve: `[[tft100-hawk]]`
  dangles. Permalink form `[[40-device-profiles/tft100-hawk]]` and exact-title
  form both resolve. Applies to inline prose links as much as to `## Relations`.
- **`reindex` does not re-walk the tree.** It rebuilds search and embeddings
  from existing database rows, so it will not pick up new files or drop
  newly-ignored ones. Changing `bmignore` needs `reset --reindex`.
- **`reset` refuses while an MCP process is live.** Stop the service, then run
  it in a one-off container:
  ```sh
  docker compose stop
  printf 'y\n' | docker compose run --rm --no-deps -T \
      --entrypoint basic-memory basic-memory reset --reindex
  docker compose up -d
  ```
- **Reranking is opt-in.** `reranker_enabled` defaults to false upstream, which
  measures raw hybrid fusion. It is on here. Changing reranker settings does
  not require a reindex; they do not touch stored embeddings.
- **Notes with no frontmatter get no permalink** and index as `permalink: null`,
  which makes them unaddressable by `memory://` and `read_note`.
  `ensure_frontmatter_on_sync` is on to prevent that.
- **Postgres and pgvector buy nothing here.** Upstream measured identical
  vector rankings to four decimal places across sqlite-vec, pgvector and
  Milvus Lite. The vector store is a storage choice, not a quality one.
