# Zed MCP secrets: reusing `GITHUB_MCP_PAT`

## Conclusion

**Do not put `GITHUB_MCP_PAT`, `$GITHUB_MCP_PAT`, or `${GITHUB_MCP_PAT}` in Zed's `settings.json` `env` object.** Current Zed has no documented settings-file environment-variable interpolation syntax. Its current stdio-MCP implementation passes configured `env` strings directly to the child command; it does not expand them. Therefore, the following would give the server the literal string `$GITHUB_MCP_PAT`, not the token:

```jsonc
"env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "$GITHUB_MCP_PAT" }
```

Zed *does* pass its own inherited process environment to child processes by normal OS process inheritance. The GitHub MCP server does **not** read `GITHUB_MCP_PAT`; its documented/current source input is `GITHUB_PERSONAL_ACCESS_TOKEN`. Reuse `GITHUB_MCP_PAT` safely by replacing the extension entry with a local/stdio command that runs the server through `fnox exec` and maps the variable at run time. This is more reliable than depending on Zed's inherited environment because fnox loads secrets from the encrypted local cache on each interactive prompt, while Zed's GUI environment capture is only documented as a login shell. No token is stored in tracked configuration.

## Relevant Zed configuration context

| Concern | Current Zed mechanism | Result |
| --- | --- | --- |
| Local GitHub MCP server | `context_servers.<name>` with flat `command`, `args`, and optional `env` | **Correct context.** Zed's official MCP documentation shows this shape. |
| Remote MCP server | `context_servers.<name>.url` and optional literal `headers` | Not appropriate for a PAT here: there is no documented header interpolation. Omitting `Authorization` invokes MCP OAuth when the server supports it. |
| External/ACP agent executable | `agent_servers` | **Not** the configuration for a Zed-managed GitHub MCP server. |
| MCP extension | Extension registration plus extension-defined `settings` | No universal GitHub-token key; an extension's schema decides it. Zed docs note that the GitHub MCP extension asks for a PAT. Avoid a tracked extension setting unless its current schema documents a non-secret reference. |
| Built-in GitHub/git-hosting integration | Separate from MCP | Not evidence that the GitHub MCP server receives this PAT. |

Sources: Zed's [MCP documentation](https://zed.dev/docs/ai/mcp) (local/remote shapes and GitHub-extension note); current [MCP settings Rust schema](https://github.com/zed-industries/zed/blob/main/crates/project/src/project_settings.rs) (`Stdio`, `Http`, and `Extension` variants).

### Installed configuration and extension

This machine runs Zed 1.16.2 and currently uses the `mcp-server-github` extension form: `context_servers.mcp-server-github.settings.github_personal_access_token`. The installed extension is [LoamStudios/zed-mcp-server-github](https://github.com/LoamStudios/zed-mcp-server-github), version 0.1.0. Its [current source](https://github.com/LoamStudios/zed-mcp-server-github/blob/main/src/mcp_server_github.rs) deserializes `github_personal_access_token` as a required `String` and puts that string directly into the child command's `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable. It has no interpolation or inherited-environment fallback. The existing extension entry therefore cannot be tracked safely and must be replaced, not merely edited to contain `$GITHUB_MCP_PAT`.

## The four distinct mechanisms

1. **Zed process environment — supported.** If launched with `zed` from a shell, Zed inherits that shell's variables. For GUI/launcher starts, Zed obtains an environment by running a login shell. Zed documents that process environment is inherited by spawned processes. Ensure the secret loader exports `GITHUB_MCP_PAT` into the environment visible to the **Zed process**; a project-only `.env`, `direnv`, or terminal-only environment is not a safe assumption for this MCP start path. [Zed environment documentation](https://zed.dev/docs/environment)

2. **Settings-file interpolation — not supported/documented for this use.** No official Zed setting or MCP documentation defines `$VAR`, `${VAR}`, `${env:VAR}`, `${input:...}`, or a keychain-reference syntax for `context_servers.*.env`, `headers`, `command`, or extension settings. The current stdio transport builds the command and calls `command.envs(binary.env.unwrap_or_default())`; it performs no expansion before spawning. [Current implementation](https://github.com/zed-industries/zed/blob/main/crates/context_server/src/transport/stdio_transport.rs)

   In particular, GitHub MCP documentation's examples such as `$GITHUB_PAT` and `${input:github_token}` are explicitly **host-dependent** examples, not Zed syntax. Its README says configuration environment-variable support varies by host. [GitHub MCP README](https://github.com/github/github-mcp-server#handling-pats-securely)

3. **Spawning an MCP server with environment variables — supported, but literal.** `context_servers.<name>.env` adds literal name/value pairs to the local stdio server process. It can contain non-secret constants, but cannot rename `GITHUB_MCP_PAT` to the server's required variable without an actual shell/wrapper process. The child otherwise inherits Zed's process environment. [Zed MCP docs](https://zed.dev/docs/ai/mcp); [stdio transport source](https://github.com/zed-industries/zed/blob/main/crates/context_server/src/transport/stdio_transport.rs)

4. **Zed credentials/keychain — limited to the right auth flow.** Zed stores LLM-provider keys in the system keychain, not `settings.json`, but that is not a generic secret-reference feature for arbitrary stdio-MCP `env` values. For HTTP MCP servers without a static `Authorization` header, Zed runs standard MCP OAuth and persists the OAuth session in the keychain. This can avoid a PAT only when the *remote MCP endpoint* supports that OAuth flow; it does not inject a GitHub PAT into the local GitHub MCP server. [Zed API-access docs](https://zed.dev/docs/ai/use-api-access); [MCP docs](https://zed.dev/docs/ai/mcp); [MCP OAuth/keychain source](https://github.com/zed-industries/zed/blob/main/crates/project/src/context_server_store.rs)

## Recommended tracked configuration (local GitHub MCP server)

Replace the extension entry with the official custom stdio shape below. The outer login shell changes to `$HOME` so fnox finds `~/fnox.toml`; `fnox exec` loads `GITHUB_MCP_PAT` from the encrypted machine-local cache even when Zed did not inherit a prompt-loaded environment. The inner shell maps it to the name required by GitHub MCP. Docker is already installed on this machine.

```jsonc
{
  "context_servers": {
    "github": {
      "command": "/bin/bash",
      "args": [
        "-lc",
        "cd \"$HOME\" && exec fnox --non-interactive exec --replace -- /bin/sh -c 'test -n \"${GITHUB_MCP_PAT:-}\" || { echo \"GITHUB_MCP_PAT is unavailable from fnox\" >&2; exit 1; }; export GITHUB_PERSONAL_ACCESS_TOKEN=\"$GITHUB_MCP_PAT\"; exec docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server'"
      ]
    }
  }
}
```

The tracked text contains only variable names. The token flows as: encrypted fnox local cache -> `fnox exec` environment -> `/bin/sh` mapping -> Docker client -> container. The `-e GITHUB_PERSONAL_ACCESS_TOKEN` flag passes the mapped variable into the container without putting its value in argv or settings. The GitHub MCP server documents `GITHUB_PERSONAL_ACCESS_TOKEN` for PAT authentication, and its current `main.go` obtains `personal_access_token` through Viper with the `GITHUB_` environment prefix; it does not name `GITHUB_MCP_PAT`. [GitHub README](https://github.com/github/github-mcp-server); [current server source](https://github.com/github/github-mcp-server/blob/main/cmd/github-mcp-server/main.go)

The on-demand fnox load and variable mapping were verified locally without printing either value. If using a separately managed `github-mcp-server` binary instead of Docker, keep the same fnox wrapper and replace the `exec docker ...` portion with `exec github-mcp-server stdio`.

### Safer operational pattern

- Keep the value only in the existing non-tracked fnox/local-cache model, never in Zed settings, a tracked shell file, or command arguments.
- Use `fnox --non-interactive exec` for GUI-launched services so startup fails clearly instead of prompting or silently starting without credentials.
- Use a least-privileged, dedicated token and GitHub MCP `--read-only`/tool-selection options where appropriate. The GitHub MCP server warns that it can call many GitHub APIs. [GitHub README](https://github.com/github/github-mcp-server)
- Do not use a remote `headers.Authorization: "Bearer ${GITHUB_MCP_PAT}"` pattern. It is neither documented nor supported as Zed interpolation. Use that remote server's OAuth path instead when available.

## Version/schema caveats

- This finding is based on current official docs and the repositories' `main` branches consulted for this report. Zed's MCP format has changed before; use **Settings -> AI -> MCP Servers** or `zed: open settings file` and validate against the installed release's settings editor after upgrading.
- The current source models context-server types with a `source` discriminator internally, while current official docs show the user-facing flat local form above. Follow the official docs/generated UI for the installed Zed version rather than adding an undocumented discriminator solely because it appears in source.
- GitHub MCP documentation may show interpolation forms for VS Code, Gemini CLI, or other hosts. They are not portable to Zed. `GITHUB_MCP_PAT` is a host/user convention; GitHub MCP's current PAT variable is `GITHUB_PERSONAL_ACCESS_TOKEN`.
- Zed's keychain support for HTTP MCP OAuth does not establish a general keychain placeholder for arbitrary `context_servers` values. No such placeholder syntax is recommended here.

## Evidence and limitations

No local secret values were read or printed. This is a documentation/source review, not a live Zed or GitHub MCP launch test. The fnox load and variable mapping were tested locally, but the Docker MCP server has not yet been launched through Zed. Validate the configured server's green status indicator after applying the recommendation.
