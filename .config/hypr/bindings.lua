-- Keep only your personal keybinding overrides here. Add new bindings or
-- unbind defaults before replacing them.

-- See current bindings and descriptions:
--   omarchy menu keybindings --print

-- To disable every Omarchy default binding, set this in
-- ~/.config/hypr/hyprland.lua before require("default.hypr.omarchy"), then add
-- only the bindings you want below:
--   omarchy_default_bindings = false

-- To disable all preinstalled app/webapp bindings, set:
--   omarchy_preinstalled_bindings = false

-- Add a new binding.
-- o.bind("SUPER + SHIFT + R", "SSH", "alacritty -e ssh your-server")

-- Change an existing binding by unbinding it first, then binding the key again.
-- This example changes SUPER+SPACE from the launcher to the Omarchy root menu.
-- hl.unbind("SUPER + SPACE")
-- o.bind("SUPER + SPACE", "Omarchy menu", "omarchy-menu toggle root")

-- Disable a default binding without replacing it.
-- hl.unbind("SUPER + SHIFT + B")

-- Logitech MX Keys examples:
-- o.bind("SUPER + SHIFT + S", nil, "omarchy-capture-screenshot")
-- o.bind("SUPER + H", nil, "voxtype record toggle")
-- o.bind("SUPER + PERIOD", nil, "omarchy-shell shell toggle omarchy.emojis")

-- Special workspaces (was SUPER+S scratchpad by default)
hl.unbind("SUPER + S")
o.bind("SUPER + S", "Toggle Slack Special Workspace", hl.dsp.workspace.toggle_special("slack"))
o.bind("SUPER + Q", "Toggle Altus (WhatsApp) Workspace", hl.dsp.workspace.toggle_special("altus"))

-- Cloud SQL Tracker panel (was: Calculator).
-- Toggles the io.github.golgor.cloud-sql-tracker bar widget's dropdown.
-- A named toggle rather than "SUPER + CTRL + <n>" (togglePanelAt right n),
-- because the numbered form is positional: it would follow whatever panel
-- happens to sit first in the bar's right section.
hl.unbind("SUPER + CTRL + Q")
o.bind("SUPER + CTRL + Q", "Cloud SQL Tracker", "omarchy-shell shell toggle io.github.golgor.cloud-sql-tracker")

-- Google Maps moved from SUPER+SHIFT+S to SUPER+SHIFT+M (was: Music/spotify;
-- cliamp remains on SUPER+SHIFT+ALT+M).
hl.unbind("SUPER + SHIFT + M")
o.bind("SUPER + SHIFT + M", "Google Maps", { webapp = "https://maps.google.com/", focus = true })

-- Audio panel in the bar on SUPER+SHIFT+S (was: Google Maps).
hl.unbind("SUPER + SHIFT + S")
o.bind("SUPER + SHIFT + S", "Audio panel", "omarchy-shell shell toggle omarchy.audio")
