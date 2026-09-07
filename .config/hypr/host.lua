-- Shared host detection for per-machine Hyprland config.
-- Returns the trimmed /etc/hostname, or "" if unreadable.
local function hostname()
	local f = io.open("/etc/hostname")
	if not f then
		return ""
	end
	local h = f:read("*l") or ""
	f:close()
	return (h:gsub("%s+$", ""))
end

return { hostname = hostname }
