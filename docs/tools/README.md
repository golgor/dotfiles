# Tool Documentation

Documentation for key development tools, CLIs, and coding agent harnesses configured and tracked in this dotfiles repository.

## Catalog

| Tool | Binary | Backend | Config / Notes | Doc |
| --- | --- | --- | --- | --- |
| backpass | `backpass` | `npm:backpass` (+ `npm:acpx`) | `.backpass/` (project), `~/.config/backpass/` (user) | [backpass.md](backpass.md) |
| DBX MCP | `dbx-mcp-server` | `npm:@dbx-app/mcp-server` (+ `aur:dbx-bin` desktop) | `~/.local/share/com.dbx.app/` (machine-local) | [dbx.md](dbx.md) |
| Oh My Pi | `omp` | `github:can1357/oh-my-pi` | `~/.omp/` (global), `.omp/` (project) | [omp.md](omp.md) |

## Notes

| Note | Read before | Doc |
| --- | --- | --- |
| Agent session lessons | changing the harness system prompt — staging area for candidate prompt rules | [agent-session-lessons.md](agent-session-lessons.md) |

For Agent eXperience Interface (AXI) specific tools, see [docs/axi/README.md](../axi/README.md).
