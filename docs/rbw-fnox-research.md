# rbw + fnox: why you get master-password prompts, and what to do about it

> **Update (2026-09-09):** the setup has since moved to "Option C" — the age
> sync cache was dropped in favour of the fnox `[daemon]` (in-memory cache) plus
> rbw's own encrypted offline vault, with silent unlock via
> `rbw-pinentry-keyring`. The fnox manifest now lives in the tracked
> `~/.config/fnox/config.toml`, which fnox reads from every directory. See issue
> #29 and the PR that closed it. The report below is the original, historical.

Research report, 2026-09-06. **No configuration was changed.** Facts marked
_verified_ were checked against primary sources (linked) or reproduced on this
machine; anything else is labelled as inference.

> Side effect of the research: the experiments ran `rbw lock`, so the agent is
> currently locked. The next `fs`/`rbw unlock` will prompt once. Nothing else
> was touched.

---

## TL;DR

1. **Your fnox cache works.** With rbw locked, `fnox get` and the shell hook
   resolved all five secrets from the age cache without contacting rbw at all
   (verified on this machine, and in fnox's source: a `sync` field _replaces_
   the Bitwarden provider, it does not fall back to it).
2. **The prompts come from four places**, none of them "the cache is broken":
   - `fs` → `rbw unlock`, every time the agent has been idle > 1 h (`lock_timeout = 3600`).
   - Any secret in `~/fnox.toml` that is **not yet in `~/fnox.local.toml`**
     (new secret added, or second machine before its first `fs`). The shell
     hook then calls `rbw get` for it **on every prompt** until you sync.
   - fnox resolves uncached secrets **in parallel**, and rbw-agent spawns **one
     pinentry per concurrent client**. Five uncached secrets = five password
     dialogs. That was the "type the same password many times" episode.
   - Bitwarden items with **"Master password re-prompt"** enabled prompt on
     every `rbw get` even when the vault is unlocked (rbw ≥ 1.14). Worth a
     one-time check of your five items.
3. **"Agent" = `rbw-agent`.** It is a per-user background process (like
   `ssh-agent`) that rbw starts on demand, holding your vault keys in RAM. It
   is not a systemd unit and not a fnox thing. fnox _also_ has an optional
   daemon, but it is opt-in and **not running** on your machine.
4. **Recommendation, in order:**
   - **Step 1 (5 min, no new moving parts):** raise `lock_timeout` to
     something like 30 days. Type the master password once per boot.
   - **Step 2 (15 min, zero prompts):** use rbw's own
     `rbw-pinentry-keyring` script as the pinentry, storing the master password
     in GNOME Keyring. On this machine that keyring is plaintext-on-LUKS, i.e.
     the same protection level as your existing `~/.config/fnox/age.txt` — so
     this is **not** a step down from where you are today.
   - Keep rbw and fnox. Switching to `bw` would be worse for this use case.
   - Remove the unused `rbw-work` alias, or wire the work vault as a second
     fnox provider with `profile = "work"` (the keyring script is profile-aware).

---

## 1. How rbw works

rbw is an unofficial Bitwarden CLI whose whole point is to avoid the official
CLI's statelessness. Instead of passing a `BW_SESSION` token around, it keeps a
background agent that holds the keys, "similar to the way that `ssh-agent` or
`gpg-agent` work" ([README](https://github.com/doy/rbw#rbw)).

```
  you / fnox ──▶ rbw (thin client) ──unix socket──▶ rbw-agent (daemon)
                                                    ├─ master key + org keys, in RAM only
                                                    ├─ idle timer → drops keys (lock_timeout)
                                                    ├─ sync timer → refreshes vault (sync_interval)
                                                    ├─ pinentry spawner (asks for master password)
                                                    └─ built-in SSH agent (ssh-agent-socket)
      encrypted vault copy on disk: ~/.local/share/rbw/
      sockets:                       /run/user/1000/rbw/{socket,ssh-agent-socket,pidfile}
      logs:                          ~/.local/share/rbw/agent.{out,err}
```

### The agent lifecycle _(verified: [`main.rs`](https://raw.githubusercontent.com/doy/rbw/main/src/bin/rbw-agent/main.rs), [`agent.rs`](https://raw.githubusercontent.com/doy/rbw/main/src/bin/rbw-agent/agent.rs))_

- The first `rbw` command that needs the agent starts `rbw-agent`, which
  daemonizes (double-fork). That is why `ps` shows its parent as
  `systemd --user`: the user manager is a child-subreaper, it just adopted the
  orphan. There is **no** systemd unit; nothing in `~/.config/systemd/user/`
  refers to rbw.
- It survives closing terminals and is re-spawned on demand if killed. It dies
  on logout with the user session.
- It disables `ptrace` attach and core dumps for itself (changelog 1.1.0 /
  1.15.0), so other processes of your user cannot trivially read its memory.
- `rbw stop-agent` kills it; `rbw lock` drops the keys but keeps it running.

### Locking _(verified: `main.rs`, `agent.rs`, `state.rs`, `timeout.rs`)_

- `lock_timeout` is read as `Duration::from_secs(u64)`. It is an **idle
  timer**: every successful request (`Unlock`, `Decrypt`, `Encrypt`, …) calls
  `state.set_timeout()`, which restarts the countdown. So "3600" means "lock
  after one hour of _not using rbw_", not "one hour after unlocking".
- When it fires, `state.clear()` drops the private and organisation keys. The
  next request triggers a fresh pinentry.
- `0` is rejected on purpose (changelog 0.3.0). There is no "never" value; use
  a large number. The timer is a tokio sleep, whose documented maximum is
  68 719 476 734 ms ≈ 2.2 years; modern tokio clamps rather than panics on
  larger values ([tokio docs](https://docs.rs/tokio/latest/tokio/time/fn.sleep.html),
  [tokio PR #4495](https://github.com/tokio-rs/tokio/pull/4495)). Anything up
  to one year (31 536 000) is unambiguously safe.
- Nothing locks the agent on screen lock or suspend. Only the timer,
  `rbw lock`, `rbw stop-agent`, or a server-side logout notification.

### Pinentry, and why you got five prompts at once _(verified: [`actions.rs`](https://raw.githubusercontent.com/doy/rbw/main/src/bin/rbw-agent/actions.rs), `agent.rs`)_

- The agent speaks the GnuPG **Assuan** protocol to whatever executable is in
  `rbw config`'s `pinentry` field (default `pinentry`, yours is
  `pinentry-curses`). Any executable that answers `SETPROMPT`/`SETDESC`/
  `GETPIN` works; it does not have to be a real pinentry.
- The agent handles each socket connection in its own task. `unlock_state()`
  checks `needs_unlock()` under the state mutex, **releases it, then spawns
  pinentry**. There is no "unlock in progress" gate. Consequence: N clients
  asking at the same time while locked → N pinentry processes, each wanting
  the master password. The first success unlocks the agent; the others still
  have to be answered or cancelled.
- `pinentry-curses` needs a controlling TTY. The agent is a detached daemon,
  so it only has a TTY when the _client_ passes its terminal through (rbw does
  that via the `Environment` in each request). From a process with no TTY
  (MCP server, mise task, editor plugin, CI) curses fails immediately with
  `Inappropriate ioctl for device` — the lines in your `agent.err`. A GUI
  pinentry has no such requirement, which is why switching to curses turned
  "many dialogs" into "silent failure + log line". Neither is what you want.
- The `pinentry-curses: no LC_CTYPE known` line is cosmetic.

### Master password re-prompt _(verified: rbw changelog 1.14.0/1.14.1/1.15.0, `actions.rs` `decrypt_cipher`)_

Since 1.14.0 rbw honours Bitwarden's per-item
["Master password re-prompt"](https://bitwarden.com/help/master-password-re-prompt/)
flag: decrypting such an item asks for the master password **even when the
agent is unlocked**. If any of your five API-token items has that box ticked,
every `fs` and every uncached resolution of that item prompts. Check each item
in the web vault (edit → "Master password re-prompt"). This is unrelated to
`lock_timeout` and would survive every other fix below.

### Profiles _(verified: README "Profiles")_

`RBW_PROFILE=work rbw …` uses a completely separate config, vault copy **and
agent** (`/run/user/1000/rbw-work/`). Two accounts = two unlocks, two timers.
On this machine no `work` profile is configured; the alias in `.bashrc` is
currently dead.

### SSH agent _(verified: README "SSH Agent", changelog 1.14.0/1.15.0)_

`rbw-agent` also serves SSH-key vault items on
`$XDG_RUNTIME_DIR/rbw/ssh-agent-socket`. Usage: `rbw unlock` once, then
`export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/rbw/ssh-agent-socket"`. It needs the
vault unlocked, so it benefits directly from steps 1–2 below. Caveat: Omarchy
already runs `gcr-ssh-agent`; pick one `SSH_AUTH_SOCK` per shell, don't mix.

---

## 2. How fnox uses rbw (and the cache)

Your layout is exactly fnox's documented "golden path": references in a
committed `fnox.toml`, values cached under a personal age key in the ignored
`fnox.local.toml` ([Syncing secrets locally](https://fnox.jdx.dev/guide/sync)).

### Resolution order _(verified: [`secret_resolver.rs`](https://raw.githubusercontent.com/jdx/fnox/main/crates/fnox-core/src/secret_resolver.rs), and reproduced locally)_

```rust
// try_resolve_from_provider()
// If a sync cache exists, resolve from the sync provider/value instead
let (provider_name, provider_value) = if let Some(ref sync) = secret_config.sync {
    (sync.provider.clone(), sync.value.clone())
} else { … primary provider … };
```

- A `sync` field **replaces** the primary provider. If age decryption fails
  (missing key, wrong recipient) fnox reports an error per `if_missing`; it
  does **not** silently fall through to Bitwarden. Good: no hidden rbw calls.
- Reproduced: with rbw locked, `fnox get FLESPI_TOKEN` and a fresh
  `fnox hook-env` produced the values and added **zero** lines to
  `agent.err`.
- The shell hook (`_fnox_hook` in `PROMPT_COMMAND`) hashes the config and
  exits early with "no changes detected" on every subsequent prompt. Per-prompt
  cost is one fast process; secrets are not re-resolved.
- Config discovery walks **up** from the cwd. From `/tmp` only the global
  `~/.config/fnox/config.toml` is found (no secrets); from anywhere under
  `~` it finds `~/fnox.toml` + `~/fnox.local.toml`. That is fine for your use.

### The batch path — where the prompts come from _(verified: `secret_resolver.rs` `resolve_secrets_batch`, reproduced locally)_

Secrets **without** a `sync` field are grouped by provider and resolved
together ("Resolving 3 secrets from provider 'bitwarden' using batch"). The
Bitwarden provider runs one `rbw get <item> [--field <f>]` per secret,
concurrently. Reproduced with three uncached secrets and a locked agent: three
`rbw get` within 1 ms, three pinentry spawns, three `Inappropriate ioctl`
lines. Adding `--non-interactive` did **not** stop it — fnox's non-interactive
guard only applies to providers that declare `requires_interactive_auth`, and
the Bitwarden provider does not.

`auth_command = "rbw unlock"` only kicks in **after** the parallel attempts
have failed and only when fnox has a TTY (`try_resolve_with_auth_retry` →
`prompt_and_run_auth`). It is a recovery prompt, not a pre-flight unlock.

So the real-world triggers on your machine are:

| Trigger | What happens | Frequency |
|---|---|---|
| `fs` after > 1 h idle | `rbw unlock` → one prompt (by design) | every sync |
| Secret added to `fnox.toml`, `fs` not yet run | hook resolves it via rbw on **every prompt**; `rbw get` prompts if locked | until you sync |
| Second machine, first shell after `git pull` | all new secrets uncached → N parallel prompts | once per machine per change |
| Item has "master password re-prompt" | prompt on every `rbw get` of that item | every sync |
| Non-TTY caller (MCP, mise task) with uncached secret | curses pinentry fails silently; secret missing | as above |

### The fnox daemon _(verified: [Cache secrets in memory](https://fnox.jdx.dev/guide/daemon), `fnox daemon status`)_

Opt-in (`[daemon] enabled = true` or `FNOX_DAEMON=on`), memory-only cache of
resolved values, idle timeout, Unix socket. **Not running here** and not
needed: the age cache already makes reads local and fast. You can ignore it.

---

## 3. Options to stop the prompts

### Option A — long `lock_timeout` (recommended first step)

`rbw config set lock_timeout 2592000` (30 days) or `31536000` (1 year).
Master password once per boot (the agent dies at logout), then never.

- Verified safe range; idle-based so a busy machine effectively never locks.
- Keys live only in `rbw-agent` RAM (ptrace-protected). Nothing new on disk.
- Does **not** help: the parallel-prompt burst on a fresh machine (still one
  round of prompts), the re-prompt flag, non-TTY callers before first unlock.

### Option B — master password from GNOME Keyring via `rbw-pinentry-keyring` (recommended second step)

rbw ships this script in its repo
([`bin/rbw-pinentry-keyring`](https://raw.githubusercontent.com/doy/rbw/main/bin/rbw-pinentry-keyring),
changelog 1.8.0, reworked 1.10.3). It is **not** in the Arch package
(`pacman -Ql rbw` has only the two binaries and completions), so it would be
copied to `~/.local/bin/` — a natural fit for the dotfiles repo.

How it works: it is itself a pinentry. On `GETPIN` with prompt
`Master Password` it runs
`secret-tool lookup application rbw profile rbw type master_password`. If the
keyring has no entry yet, it calls the real `pinentry` once (GUI on Wayland via
the `/usr/bin/pinentry` dispatcher → `pinentry-gnome3` → `gcr-prompter`, all
installed here) and **stores** the answer. Any other prompt (2FA code,
API-key registration) is passed through to the real pinentry. It honours
`RBW_PROFILE`, so a `work` profile gets its own keyring entry.

Effects:
- Every unlock — including the five-parallel burst and non-TTY callers — is
  answered instantly and silently. `lock_timeout` becomes irrelevant to your
  experience (keep it long anyway to avoid needless KDF work).
- `secret-tool` and `gnome-keyring-daemon` are present and the daemon is
  running with the secrets component (verified).

Security, honestly, **on this machine**:
- Your default keyring is the **textual, passwordless** format (`[keyring]`
  header in `Default_Keyring.keyring`, `Locked = false` over D-Bus). That is
  the Omarchy default with SDDM autologin; your own note
  `~/Documents/Personal/IT Setup/omarchy-keyring-login-prompt.md` documents the
  choice. So the master password would be **plaintext at rest, protected by
  LUKS and file permissions** — exactly the protection your
  `~/.config/fnox/age.txt` (and the SSH keys, kube tokens etc.) already have.
  Option B is therefore neither stronger nor weaker than today; it is the same
  tier, with a cleaner mechanism than a bespoke password file (standard API,
  official script, per-profile, revocable with `rbw-pinentry-keyring --clear`).
- If you ever move the keyring to the encrypted format (Option A/C in your
  note), the rbw entry becomes encrypted at rest for free.
- Threat model recap: powered-off laptop → LUKS protects all of these
  equally. Unlocked session with a hostile process → all of A/B/C/age.txt are
  equally lost. The remaining difference is only "how many copies of a
  reusable secret sit on disk", and you already accepted that with age.

### Option C — plaintext password file / stdin

rbw has **no** `--password-file`, env var or stdin path for `unlock`
(verified in `actions.rs`: every password comes from `pinentry::getpin`). A
file-based variant would just be Option B's script with `cat` instead of
`secret-tool`. No advantage; skip.

### Option D — systemd user unit that unlocks at login

Only works on top of B (needs a non-interactive pinentry). Useful if you want
the SSH agent ready before the first terminal, e.g.
`ExecStart=rbw unlock` `After=graphical-session.target`. Nice-to-have, not
needed for the prompt problem.

### Option E — flip the cache logic upside down (fnox-only)

Make the age cache the primary and Bitwarden a sync source is not how fnox
models it; `sync` already means "read local first". The one fnox-side
improvement worth considering is **unblocking the "new secret before sync"
window**: e.g. run `fs` as part of pulling dotfiles, or give new secrets a
`default = ""` so the hook stops hammering rbw until you sync. Low value once
B is in place.

---

## 4. rbw vs `bw` vs Secrets Manager

| | rbw (current) | official `bw` | Bitwarden Secrets Manager (`bws`) |
|---|---|---|---|
| Auth model | agent holds keys; pinentry | `BW_SESSION` token per shell; you persist it yourself | machine access token |
| Offline | encrypted vault copy on disk, works offline | needs login state; slower Node start-up | network |
| Unlock prompt avoidance | pluggable pinentry (Option B) | `bw unlock --passwordenv/--passwordfile`, or persist `BW_SESSION` (no expiry until `bw lock`; [forum](https://community.bitwarden.com/t/cli-session-expiration/43611)) | none needed |
| fnox support | `backend = "rbw"` (documented as experimental, but works) | default backend | separate `bitwarden-sm` provider |
| Scope | your Personal vault + org collections | same | **separate product**; secrets must be re-created there; requires an org with the SM add-on, not part of personal Premium (verify current tiers) |
| Extras | SSH agent, TOTP | TOTP | — |

Why you probably chose rbw: `bw` makes you juggle `BW_SESSION` in every shell
and MCP process, which is precisely the "stateless" pain rbw's README calls
out. For "five API tokens into env vars on two workstations", rbw + fnox's age
cache is the simplest correct design. Secrets Manager only becomes interesting
if the company org already pays for it **and** you are happy to move the
tokens there; it does nothing for personal items.

### The work vault

- If the company set-up is an **organisation your personal account belongs
  to**, its collections already show up in your vault and rbw sees them (rbw
  unlocks org keys alongside the private key; verified in `unlock_state`).
  Then the `work` profile is unnecessary — delete the alias.
- If it is a **separate account** (different e-mail), keep
  `RBW_PROFILE=work`. fnox can target it directly: a second provider
  `bitwarden-work = { type = "bitwarden", backend = "rbw", profile = "work" }`
  sets `RBW_PROFILE` on the `rbw` calls (verified in fnox `bitwarden.rs`).
  `rbw-pinentry-keyring` stores a separate keyring entry per profile, so B
  covers both accounts. `rbw register` is needed once per profile against
  bitwarden.com (README note about bot detection).

---

## 5. Small clean-ups noticed (no action taken)

- `.bashrc` exports `FNOX_AGE_KEY_FILE`; the `sync-age` provider already has
  `key_file`. Redundant but harmless. fnox docs note `FNOX_AGE_KEY` (the
  inline key) takes precedence over `key_file`; the `_FILE` variant is fine.
- `alias rbw-work` points at a profile that does not exist.
- `~/.config/fnox/config.toml` is `0644`; it holds only the age _recipient_
  and a path, so that is fine. `age.txt` is `0600` as it should be.
- The `fs` alias is the right shape: one `rbw unlock` **before** the parallel
  `fnox sync`. Keep that ordering; running `fnox sync` alone while locked is
  what produces the burst.
- Optional hardening later, orthogonal to prompts: fnox supports
  hardware-backed age identities (TPM via `age-plugin-tpm`, FIDO2) for the
  sync cache ([docs](https://fnox.jdx.dev/guide/sync#hardware-backed-decryption)).
  That would be the first thing that actually raises the at-rest bar above
  "LUKS + file perms".

---

## 6. Suggested plan (for when you decide to act)

1. Check the five Bitwarden items for "Master password re-prompt"; untick if set.
2. `rbw config set lock_timeout 2592000` on both machines. Observe for a week.
3. Add `rbw-pinentry-keyring` to `~/.local/bin` via the dotfiles repo,
   `rbw config set pinentry rbw-pinentry-keyring`, run `rbw unlock` once (GUI
   prompt, stored in keyring). Document `rbw-pinentry-keyring --clear` as the
   revoke step.
4. Decide on the work vault: delete the alias, or add a `profile = "work"`
   fnox provider and register the profile.
5. Optional: `SSH_AUTH_SOCK` → rbw's socket for Bitwarden-stored SSH keys.

Each step is independently reversible (`rbw config unset lock_timeout`,
`rbw config unset pinentry`).

---

## 7. Method and caveats

- Local facts: `rbw config show`, `pacman -Ql rbw`, `agent.err`, PAM and SDDM
  config, keyring file header and D-Bus `Locked` property, `fnox config-files`
  from several directories, `fnox -v` traces, and controlled experiments in a
  temp directory with rbw locked (three uncached secrets, with and without
  `--non-interactive`).
- Primary sources: rbw README/CHANGELOG and agent source (`main.rs`,
  `agent.rs`, `actions.rs`, `state.rs`, `timeout.rs`, `bin/rbw-pinentry-keyring`);
  fnox docs (Bitwarden provider, Syncing, Daemon) and `secret_resolver.rs`,
  `providers/bitwarden.rs`; Bitwarden help (master password re-prompt, CLI);
  tokio `sleep` docs.
- Three opus sub-agent research lanes were launched but had no web access in
  their sandbox; their output was used only as a checklist of hypotheses, every
  claim above was re-verified directly.
- Not verified: current Bitwarden Secrets Manager tiering/pricing; whether
  your company org is a separate account or a membership of your personal
  account; whether any of the five items has the re-prompt flag (agent was
  locked during research).
