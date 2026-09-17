-- Extra autostart processes.
-- o.launch_on_start("my-service")

-- Nightlight schedule lives in hyprsunset.conf; hyprsunset must be running for it.
o.launch_on_start("hyprsunset")

-- Slack, only on this laptop. The wrapper waits for network + an external
-- monitor before launching (see ~/.local/bin/slack-delayed-start), replacing the
-- XDG autostart that started Slack too early.
if require("hypr.host").hostname() == "golgor-framework" then
	o.launch_on_start("slack-delayed-start")
end
