# kubernetes-axi

Agent-facing Kubernetes operations: discover, inspect, deploy, debug, scale, roll
out, expose, clean up. Read-only/dry-run by default; mutations need `--execute`,
deletes also need `--confirm <exact-name>`. Redacts secrets and kubeconfig creds.

- Source: <https://github.com/thatdudealso/kubernetes-axi>
- npm: **not published** (registry returns 404 as of this writing)
- Command: `./bin/kubernetes-axi.js` (from the clone)

## Why it is not in mise

The other axi tools are npm packages installed through mise's npm backend.
`kubernetes-axi` is **not on npm**, so there is no `"npm:kubernetes-axi"` entry in
`.config/mise/config.toml`. It is documented here but not deployed. Revisit and
add the mise entry if/when it publishes to npm.

## Requirements

- Node 20+.
- `kubectl` — already in `.config/mise/config.toml`.

## Manual install (per machine, not tracked)

```sh
git clone https://github.com/thatdudealso/kubernetes-axi.git
cd kubernetes-axi
npm install
./bin/kubernetes-axi.js doctor
```

Add a `PATH` entry or alias for `./bin/kubernetes-axi.js` if you want it on the
shell directly. This is per-machine state; mise does not manage it.

## Usage

```sh
./bin/kubernetes-axi.js discover
./bin/kubernetes-axi.js list --kind pods
./bin/kubernetes-axi.js plan --target <id> --environment local
./bin/kubernetes-axi.js apply --target <id> --execute
./bin/kubernetes-axi.js delete --kind deployment --name <name> --confirm <name> --execute
```

Mutations are dry-run until `--execute`; review the generated command and
preflight output first.

## Hooks

Per its upstream README, `kubernetes-axi hooks install --agent all --scope project --execute` installs ambient session-context hooks (opt-in). Unverified here — kubernetes-axi is clone-only (not installed), so confirm the exact command with `kubernetes-axi hooks --help` after cloning.
</content>
