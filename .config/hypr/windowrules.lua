-- Converted from windowrules.conf

-- Always open Slack on special workspace named "slack"
hl.window_rule({
	name = "slack-special-workspace",
	match = { class = "^(slack)$" },
	workspace = "special:slack",
})

hl.window_rule({
	name = "altus-special-workspace",
	match = { class = "^(Altus)$" },
	workspace = "special:altus",
})

hl.window_rule({
	name = "slack-rounding",
	match = { class = "^(slack)$" },
	rounding = 10,
})

hl.window_rule({
	name = "slack-animation",
	match = { class = "^(slack)$" },
	animation = "slide",
})

o.window("^com\\.jankeesvw\\.OmarchyMeetingRecorder$", { float = true })
o.window("^com\\.jankeesvw\\.OmarchyMeetingRecorder$", { size = { 480, 700 } })
o.window("^com\\.jankeesvw\\.OmarchyMeetingRecorder$", { center = true })
