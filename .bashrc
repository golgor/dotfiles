# shellcheck shell=bash
# If not running interactively, don't do anything (leave this at the top of this file)
[[ $- != *i* ]] && return

# All the default Omarchy aliases and functions
# (don't mess with these directly, just overwrite them here!)
source /usr/share/omarchy/default/bash/rc

# ── mise: shim-first PATH for agent-launched harnesses only ────────────────
# Omarchy's default/bash/init runs `mise activate bash` (hook mode) for this
# interactive shell. That's correct here: it's what injects mise [env]/_.file
# secrets (e.g. project .env vars) on `cd`, and a human's PATH does update on the
# next prompt anyway. Leave it alone.
#
# But an agent harness (claude/pi/codex) freezes whatever PATH mise resolved at
# launch and never re-resolves after that — its own Bash-tool calls are
# non-interactive, so the hook never fires again. If the agent later works in a
# directory pinning a different tool version than its launch directory, every
# command after that silently uses the wrong version.
#
# Fix: launch the agent with a PATH that has mise's *shims* dir first instead of
# a frozen install dir. Each shim re-resolves the correct version per directory,
# on every invocation, for the life of the session — no relaunch needed.
#
# One catch: a mise shim is a symlink to `mise` itself (`readlink shims/claude`
# -> /usr/bin/mise). Looking the agent up by name would resolve through its own
# shim, and mise would rebuild *its* PATH with install dirs prepended again,
# re-poisoning the long-lived agent process right at the start. So resolve the
# absolute binary first (`mise which`) and exec that directly — never let the
# agent's own name go through PATH lookup. Only safe for native-binary CLIs
# (verified: claude, pi, codex are all ELF binaries, not shebang scripts).
_mise_agent_path() {
	local p= d
	local IFS=:
	for d in $PATH; do
		[[ $d == *"/.local/share/mise/installs/"* ]] || p+="${p:+:}$d"
	done
	printf '%s:%s' "$HOME/.local/share/mise/shims" "$p"
}

_mise_agent_run() {
	local name=$1
	shift
	local bin
	bin=$(mise which "$name" 2>/dev/null) || bin=$(type -P "$name")
	[ -x "$bin" ] || {
		printf '%s: not found\n' "$name" >&2
		return 127
	}
	env PATH="$(_mise_agent_path)" "$bin" "$@"
}

claude() { _mise_agent_run claude "$@"; }
pi() { _mise_agent_run pi "$@"; }
codex() { _mise_agent_run codex "$@"; }
# ───────────────────────────────────────────────────────────────

alias c="clear"
alias tree="eza -T --icons=always --color=always --group-directories-first --git-ignore --no-quotes"
alias src="source ~/.bashrc"
alias br="nvim ~/.bashrc"
alias task="go-task"
alias rbw-work="RBW_PROFILE=work rbw" # separate Bitwarden account, work vault
alias pm='cd ~/Documents/ToolSense && pi --append-system-prompt ./SYSTEM.md'
alias cq='cloud-sql-tracker'

# Override Omarchy's try default (~/Work/tries) with Code/Sketches.
# `command try` bypasses Omarchy's lazy wrapper function.
if command -v try &>/dev/null; then
	eval "$(SHELL=/bin/bash command try init "$HOME/Code/Sketches")"
fi

# Set up for Gnome Keyring to handle SSH-keys (enable ssh-add -l to use gnome keyring)
export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/gcr/ssh"

# Set Google Cloud Project for Gemini CLI
export GOOGLE_CLOUD_PROJECT="toolsense"

# Set up GOPRIVATE to enable installing from toolsense repos
export GOPRIVATE="go.iot.toolsense.dev/*","go.iot.toolsense.io/*"

# grok CLI (completions live in ~/.bash_completions.d/grok)
export PATH="$HOME/.grok/bin:$PATH"

# Omarchy already inits zoxide with z/zi; re-init with --cmd cd so plain
# `cd` is the smart one.
if command -v zoxide &>/dev/null; then
	eval "$(zoxide init bash --cmd cd)"
fi

# Shell history (installed via mise, not part of Omarchy).
if command -v atuin &>/dev/null; then
	eval "$(atuin init bash)"
fi

# Initialize yazi. Enable cd from yazi, and use y.
function y() {
	local tmp cwd="" status
	tmp="$(mktemp -t "yazi-cwd.XXXXXX")" || return

	yazi "$@" --cwd-file="$tmp"
	status=$?
	IFS= read -r -d '' cwd <"$tmp" || true

	if [[ -n $cwd && $cwd != "$PWD" ]]; then
		builtin cd -- "$cwd" || status=$?
	fi

	rm -f -- "$tmp" || status=$?
	return "$status"
}

# Bash completions
if [ -d ~/.bash_completions.d ]; then
	for file in ~/.bash_completions.d/*; do
		[ -f "$file" ] && source "$file"
	done
fi

# fnox: age-encrypted local cache, auto-loaded from ~/fnox.toml on every prompt.
# Machine-local setup (age key, sync-age provider) comes from: mise run setup-fnox
if command -v fnox &>/dev/null; then
	export FNOX_AGE_KEY_FILE=~/.config/fnox/age.txt
	# fnox activate bakes its resolved versioned path, which mise deletes on
	# upgrade, breaking every open shell. Rewrite to the stable 'latest' symlink.
	if fnox_activation="$(fnox activate bash)" &&
		fnox_activation="$(sed 's|/mise/installs/fnox/[^/]*/fnox|/mise/installs/fnox/latest/fnox|g' <<<"$fnox_activation")"; then
		eval "$fnox_activation"
	else
		printf 'warning: fnox shell activation failed\n' >&2
	fi
	unset fnox_activation
fi

alias fs='cd ~ && rbw unlock && fnox sync --provider sync-age --local-file --force'
