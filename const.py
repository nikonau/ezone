"""Constants for the EZone integration."""

DOMAIN = "ezone"

# EZone API constants
EZONE_STATE_ON = "1"
EZONE_STATE_OFF = "0"

# Climate modes (based on your YAML)
EZONE_HVAC_MODES = {
    "1": "cool",      # Cool mode
    "2": "heat",      # Heat mode  
    "3": "fan_only",  # Fan mode
}

# Fan modes (based on your YAML)
EZONE_FAN_MODES = {
    "1": "low",       # Fan low
    "2": "medium",    # Fan medium (default)
    "3": "high",      # Fan high
}

# Zone states
ZONE_ON = "1"
ZONE_OFF = "0"