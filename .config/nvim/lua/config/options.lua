require("config.remote_clipboard").setup()
-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.opt.relativenumber = false

-- Treat .bashrc as bash, not POSIX sh. Otherwise the shell LSP (shuck) parses
-- it as sh, rejects [[ ]], and floods the buffer with false "code is
-- unreachable" / "no matching opener" diagnostics.
vim.filetype.add({ filename = { [".bashrc"] = "bash" } })
