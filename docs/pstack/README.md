# pstack in this repository

This directory documents the adopted pstack skill pack. The upstream guide is preserved in [UPSTREAM.md](UPSTREAM.md); its links are rewritten for this repository.

## Install and use

The full 57-skill primary pack is selected with:

```sh
mise run deploy-skills --stack pstack
```

This only projects common skills and the selected pstack stack into the Pi, Claude Code, and Codex discovery directories. In Pi, run `/reload` after deployment.

Pi invokes skills by their native names, for example `/skill:poteto-mode` or `/skill:how`. There is no bare `/pstack` command. Profile availability is separate from skill discovery: selecting the stack makes skills discoverable; it does not make every model, adapter, or service available.

`setup-pstack` configures model choices. Importing the pack does not execute it, create labels, authenticate services, or generate setup. The Pi bridge is the native primary adapter; Claude Code and Codex adapters are documented upstream but their runtime behavior still needs local validation and is not certified here.

The shared `common/` layer remains active and the Matt stack remains the default for every no-argument deployment. `common/codebase-design` remains shared. The existing `comment-sicko` body is unchanged.

## Limits and operator controls

The upstream policy text remains callable through the adopted skills and does not silently change local operator authority. When a policy conflicts with an explicit operator instruction, surface the conflict and resolve it consciously; importing the pack is not approval to reset user choices.

The local `pr-writer` remains publication-only. Run the upstream `babysit` playbook only when explicitly requested. Optional `automations/benny` is not part of the primary 57-skill pack and is not activated, installed, or run by this repository.

See [SOURCE.md](SOURCE.md) for provenance and [LICENSE](LICENSE) for the upstream license.
