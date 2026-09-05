-- Workspace-to-monitor assignment, per machine (branched on hostname).
--
-- Hyprland routes a workspace to its bound monitor when that monitor is
-- present, and falls back to an available monitor when it's absent. So the
-- laptop layout below works both docked (external plugged in) and undocked --
-- no hand-editing when you dock at the office.

local function hostname()
	local f = io.open("/etc/hostname")
	if not f then
		return ""
	end
	local h = f:read("*l") or ""
	f:close()
	return (h:gsub("%s+$", ""))
end

local function bind(ws, monitor, is_default)
	local rule = { workspace = tostring(ws), monitor = monitor }
	if is_default then
		rule.default = true
	end
	hl.workspace_rule(rule)
end

if hostname() == "golgor-framework" then
	-- Laptop: 1-8 on the external ultrawide (DP-2), 9-10 on the built-in panel (eDP-1).
	for i = 1, 8 do
		bind(i, "DP-2", i == 1)
	end
	bind(9, "eDP-1", true)
	bind(10, "eDP-1", false)
else
	-- Stationary (golgor-pc): everything on DP-1.
	for i = 1, 10 do
		bind(i, "DP-1", i == 1)
	end
end
