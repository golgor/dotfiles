-- Workspace-to-monitor assignment for machines NOT yet managed by hyprmoncfg.
--
-- The laptop (golgor-framework) is managed by hyprmoncfg: its generated
-- hyprmoncfg-monitors.lua loads last in hyprland.lua and owns the workspace
-- rules, so nothing here applies to it. This file is a bridge for the
-- stationary until it also adopts hyprmoncfg; delete it once that's done.

local hostname = require("hypr.host").hostname

local function bind(ws, monitor, is_default)
	local rule = { workspace = tostring(ws), monitor = monitor }
	if is_default then
		rule.default = true
	end
	hl.workspace_rule(rule)
end

if hostname() ~= "golgor-framework" then
	-- Stationary (golgor-pc): everything on DP-1.
	for i = 1, 10 do
		bind(i, "DP-1", i == 1)
	end
end
