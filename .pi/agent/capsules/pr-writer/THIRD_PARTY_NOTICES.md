# Third-party notices

## HumanLayer skills

Vendored from <https://github.com/humanlayer/skills> at commit `653b6411c1f70c275a18e37673b042ff99f67ceb`:

- `plugins/visual-pr/skills/visual-pr/` → `skills/visual-pr/`, including all references.
- `plugins/show-me/skills/show-me/` → `skills/show-me/`, including agent metadata.

These directories are copied without modification. Claude plugin registration files are not included: Pi discovers the skill directories directly.

Copyright (c) 2026 HumanLayer. Licensed under the MIT License. Full copyright notice and license: [HUMANLAYER_LICENSE](HUMANLAYER_LICENSE).

Pi-specific path and artifact adapters live in the `pr-writer` agent definition. Task modes and publication authority live in `skills/gh-axi/SKILL.md`, outside the vendored directories.
