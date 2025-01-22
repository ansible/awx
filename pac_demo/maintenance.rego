package maintenance

import rego.v1

# Default rule to deny if no condition matches
default allow := false

maintenance_window := {
    "start_time": "01:00",
    "end_time": "02:00"
}

# Main rule to check if the created time is within the maintenance window
allow if {
	time_within_window(input.created, maintenance_window.start_time, maintenance_window.end_time)
}

# Helper rule to check if the time is within the maintenance window
time_within_window(created_time, start_time, end_time) if {
	parsed_time := time.parse_rfc3339_ns(created_time)
	[hour, minute, _]:= time.clock(parsed_time)

	current_time := sprintf("%02d:%02d", [hour, minute])

	current_time >= start_time
	current_time < end_time
}
