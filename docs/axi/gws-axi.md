# gws-axi

Google Workspace CLI for agents: Gmail, Calendar, Docs, Drive, Slides, Sheets
behind one command. TOON output, idempotent mutations, multi-account write
safety. Gmail `send` is intentionally out of scope — it drafts, never sends.

- Source: <https://github.com/JarvusInnovations/gws-axi>
- npm: [`gws-axi`](https://www.npmjs.com/package/gws-axi)
- Command: `gws-axi`

## Requirements

- Node 20+.
- A Google account (personal or Workspace).
- A Google Cloud project to host an OAuth client — the **bring-your-own OAuth
  client** model. A new dedicated project or an existing one both work.
- `gcloud` installed and logged in — it automates the project + API-enable steps.
  Without it, those become manual Console clicks.

This is the heaviest setup of the batch: ~10 min for a fresh project, a few minutes
reusing an existing one.

## Install

Tracked via the mise npm backend:

```toml
# .config/mise/config.toml
"npm:gws-axi" = "latest"
```

```sh
mise install
gws-axi doctor      # prerequisites + live API health
```

## Auth (per machine)

An **agent-driven, 7-step** progressive flow. Run `gws-axi auth setup` repeatedly;
it prints the next step and updates a helper page at `~/.config/gws-axi/setup.html`.
The agent runs the CLI; you do the browser/Console clicks in `setup.html` — open it
in the browser profile signed into the target Google account.

```sh
gws-axi auth setup --project <id>                # bind a project; gcloud auto-enables the APIs
# → create a Desktop OAuth client in the Console (manual), then download its JSON
gws-axi auth setup --credentials-json <path>
gws-axi auth setup --confirm-step consent_screen         # once the consent screen exists
gws-axi auth setup --confirm-step test_user_added --test-user <email>
# → obtain tokens via the browser loopback (below)
```

Tokens live under `~/.config/gws-axi/` — machine-local, never in this repo.

### Getting the tokens (browser loopback)

The final step is an OAuth loopback, split so an agent can prepare then listen:

```sh
gws-axi auth login --account <email> --no-wait   # prepare; returns a pending session
gws-axi auth login --wait                        # bind the callback server + block (5 min)
```

While `--wait` runs, a yellow **"Authenticate with Google"** button appears in
`setup.html` (only while the listener is live). Click it and approve the scopes.
Expect a **"Google hasn't verified this app"** screen — click **Advanced → Go
to … (unsafe)**; that is normal for an unverified internal OAuth app.

### Consent screen: reuse, don't disturb

The OAuth **consent screen is shared per project** (one per project, across all its
clients). If you reuse a project other services already use, **do not change its
branding, user type, or publishing status** — that would affect those services. Add
your Desktop client and mark the step done with `--confirm-step consent_screen`.

The **project only hosts the OAuth client** — it does not scope which data you
reach. Access is set by the **account that consents** plus the requested scopes, so
one project is enough no matter how many you have.

### Internal vs External, and the "7-day expiry"

- **Internal** (a Workspace domain, org accounts only): no test-user step, and
  **tokens never expire**. Best when you only use Workspace accounts.
- **External + Testing**: refresh tokens expire after **7 days**, and you must add
  test users.

gws-axi may warn *"consent screen still in Testing — token expires after 7 days."*
That is a **local assumption**, not a live check. On an **Internal** (or published)
consent screen, tokens are already permanent. Reflect that locally with:

```sh
gws-axi auth publish --confirm         # sets gws-axi's local "permanent" flag — NO Google change
gws-axi auth login --account <email>   # re-auth once so the stored token is post-flag
```

**Do not** run the full `gws-axi auth publish` walkthrough when the consent screen
is shared with other services — it would try to publish that shared screen.

## Notes

- Multi-account: with 2+ accounts authenticated, writes require `--account <email>`.
  Pin one with `export GWS_AXI_ACCOUNT=<email>` (accident boundary, not a security one).
- If you keep other Google MCP servers/skills, disable them to avoid tool ambiguity.

## Hooks

`gws-axi setup hooks` opens each agent session with the gws-axi home view (authenticated accounts, write-protection status, setup/health) as ambient context. Opt-in, idempotent, machine-local (Claude Code / Codex / OpenCode); restart the agent after. Shared hook caveats: the hooks notes in this folder's `README.md`.
</content>
