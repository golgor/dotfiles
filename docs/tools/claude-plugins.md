# Claude Code plugins

Plugins installed into Claude Code with `claude plugin ...`, one section each. This state lives in
Claude's machine-local plugin store and is not owned by mise `[tools]`, so each machine installs
its own copy with the commands below.

## fast-jev-compaction

Claude Code compaction plugin that replaces lossy `/compact` summaries with Jev-scored message
retention. Source: https://github.com/tamaratran/fast-jev-compaction

The repo documents `npm install fast-jev-compaction`, but the package is not published to the npm
registry yet. Do not add it to mise as `npm:fast-jev-compaction`; mise's npm backend resolves the
public registry and fails with `package not found`.

`TYPESAFE_API_KEY` is exported by fnox from the Bitwarden item `Typesafe AI`, field `API Key`.

```sh
export CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1
claude plugin marketplace add tamaratran/fast-jev-compaction
claude plugin install fast-jev-compaction@fast-jev-compaction
# then restart Claude Code, or run /reload-plugins
```

Leave the plugin's API key option empty during installation to use `TYPESAFE_API_KEY` from the
environment.
