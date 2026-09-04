# shellcheck shell=bash
# If not running interactively, don't do anything (leave this at the top of this file)
[[ $- != *i* ]] && return

# All the default Omarchy aliases and functions
# (don't mess with these directly, just overwrite them here!)
source /usr/share/omarchy/default/bash/rc

alias c="clear"
alias tree="eza -T --icons=always --color=always --group-directories-first --git-ignore --no-quotes"
alias src="source ~/.bashrc"
alias br="nvim ~/.bashrc"
alias task="go-task"
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

# Initalize yazi. Enable cd from yazi, and use y.
function y() {
	local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
	yazi "$@" --cwd-file="$tmp"
	IFS= read -r -d '' cwd <"$tmp"
	[ -n "$cwd" ] && [ "$cwd" != "$PWD" ] && builtin cd -- "$cwd"
	rm -f -- "$tmp"
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
	eval "$(fnox activate bash | sed 's|/mise/installs/fnox/[^/]*/fnox|/mise/installs/fnox/latest/fnox|g')"
fi

alias fs='cd ~ && rbw unlock && fnox sync --provider sync-age --local-file --force'
