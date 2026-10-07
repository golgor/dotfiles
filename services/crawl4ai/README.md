# Crawl4AI

Headless Chromium that renders a page and returns it as Markdown. pi-web-access
uses it as a `fetch_content` fallback for pages a plain HTTP fetch cannot read:
bot challenges, JavaScript-only pages, cookie walls.

```sh
cd ~/.dotfiles/services/crawl4ai
docker compose up -d
curl -s localhost:11235/health
```

Endpoint: `http://127.0.0.1:11235`. Every route except `/health` needs
`Authorization: Bearer $CRAWL4AI_API_TOKEN`. `/playground` and `/dashboard` take
the token in the bar at the top of the page.

## Wiring

| Piece | Where |
|---|---|
| Token | `CRAWL4AI_API_TOKEN` in `.config/fnox/config.toml`, Bitwarden login item `Crawl4AI`, password field. fnox exports it into every shell; compose reads it from there, and so does pi-web-access, with no token field in its config. |
| pi-web-access | `.pi/agent/web-search.json`, linked to `~/.pi/agent/web-search.json`. Fetch order `http → crawl4ai → jina`. |

pi-web-access calls `POST /md` with `{"url": ..., "f": "fit"}` and sends nothing
else, so any browser tuning has to happen on the server side.

`allowRemoteHostedProviders: true` is there for Jina only. Crawl4AI counts as
self-hosted and runs without it. Jina sees every URL that gets past Crawl4AI.

## Things that cost time to learn

- **No token, no server.** Without `CRAWL4AI_API_TOKEN` the server listens on
  the container's own loopback. The published port then resets connections
  while `docker ps` shows healthy. The compose file refuses to start without
  the variable; if you still see resets after ~20 s, look for
  `binding loopback only` in `docker compose logs`.
- **The token is baked in at container creation.** After rotating it in
  Bitwarden, open a new shell and run `docker compose up -d --force-recreate`.
- **Docker starts on demand here.** `docker.service` is disabled and only
  `docker.socket` is enabled, so after a reboot `restart: unless-stopped`
  containers stay down until something touches the Docker socket.
- **Upgrading.** The image is pinned. Read the release notes before bumping it:
  0.9 made the token mandatory and changed request validation
  (`deploy/docker/MIGRATION.md` upstream).
