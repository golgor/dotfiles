# quota-axi

Agent-ergonomic quota inspector for model and provider API headroom. Reports
available quota, usage, and reset timing as TOON, enabling dispatch logic to
choose among model candidates by remaining quota.

- Source: <https://github.com/kunchenguid/quota-axi>
- npm: [`quota-axi`](https://www.npmjs.com/package/quota-axi)
- Command: `quota-axi`

## Requirements

- Node 20+.
- Provider API credentials configured in `~/.config/quota-axi/config.toml` or
  via environment variables. No external services beyond the provider APIs.

## Install

Tracked via the mise npm backend and exempted in `~/.config/aube/config.toml`:

```toml
# .config/mise/config.toml
"npm:quota-axi" = "latest"
```

```sh
mise install
quota-axi           # report current quota headroom across providers and models
```

(Zero-install alternative: `npx -y quota-axi <command>`.)

## Role

`quota-axi` reads provider quota and usage state, formats it as TOON for
low-token consumption in agent loops, and exposes model/provider headroom
without requiring external parsing. Dispatch logic uses it to select among
candidates by remaining quota.

## Usage

```sh
quota-axi                          # show quota headroom, usage, and reset times
quota-axi status                   # current quota state (alias)
quota-axi models                   # list models with quota per provider
```

Run `quota-axi --help` for the full command list.

## Routing

`quota-axi` is available in agent dispatch decisions via the global append
prompt. Firstmate uses `quota-axi status` to choose among crew-dispatch model
candidates by remaining quota and reset windows.
