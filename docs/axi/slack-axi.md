# slack-axi

Slack CLI for agents: read, search, sweep, and safely draft. Long-lived user
token (works headless), human date ranges, inlined threads, citable permalinks.
Drafts never post without an explicit `draft send`.

- Source: <https://github.com/JarvusInnovations/slack-axi>
- npm: [`slack-axi`](https://www.npmjs.com/package/slack-axi)
- Command: `slack-axi`

## Requirements

- Node 20+.
- A Slack app with a user (`xoxp-…`) token. `auth setup` generates the app
  manifest with the required scopes pre-filled.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:slack-axi" = "latest"
```

```sh
mise install
```

Then set up auth (browser + token) — see **Auth (per machine)** below.

## Auth (per machine)

A progressive, guided flow. `slack-axi auth setup` writes an app manifest to
`~/.config/slack-axi/manifest.yaml` (+ a `setup.html` helper) with the required
user scopes and **token rotation disabled** (so the token never expires).

1. Open <https://api.slack.com/apps> → **Create New App** → **From an app
   manifest** — *not* "From scratch" (that makes an empty **Demo App** with no
   scopes). Pick your workspace, paste the manifest from
   `~/.config/slack-axi/manifest.yaml`, create.
2. **Install from the app's OAuth page, not the auto "Create & Install" popup.**
   Open the app → **OAuth & Permissions** → **Install to Workspace** → Allow. The
   auto-install popup is flaky: it can close mid-install with *"Installation was
   not completed"* and spawn **duplicate apps** on refresh. If you get
   duplicates, keep one and delete the rest (Basic Information → Delete App).
3. If the workspace requires **admin approval** for app installs, request it —
   that is a policy gate, not an error.
4. Copy the **User OAuth Token** (`xoxp-…`) from OAuth & Permissions and store it
   **yourself** (keeps the secret out of shell history and agent logs):

   ```sh
   slack-axi auth login --token xoxp-...
   slack-axi doctor            # verify workspace + scope coverage
   ```

`slack-axi auth setup --confirm-step app_created` advances the setup tracker if
you want it, but `auth login` is the step that actually authenticates.

Tokens live under `~/.config/slack-axi/` — machine-local, never in this repo.
`SLACK_AXI_TOKEN` is an env alternative for headless use.

## Notes

- `slack-axi channels` lists all conversation types you belong to, including
  private channels and group DMs.

## Hooks

`slack-axi setup hooks` opens each agent session with the slack-axi home view (active workspace + channel count) as ambient context. Opt-in, idempotent, machine-local (Claude Code / Codex / OpenCode); restart the agent after. Shared hook caveats: the hooks notes in this folder's `README.md`.
</content>
