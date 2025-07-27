# EZone Integration Installation Package

## Directory Structure
Create this structure in your Home Assistant config directory:

```
/config/custom_components/ezone/
```

## Files to Create

### 1. manifest.json
```json
{
  "domain": "ezone",
  "name": "EZone",
  "codeowners": ["@yourusername"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/yourusername/ha-ezone",
  "homekit": {},
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/yourusername/ha-ezone/issues",
  "requirements": ["aiohttp"],
  "ssdp": [],
  "version": "1.0.0",
  "zeroconf": []
}
```

### 2. strings.json
```json
{
  "config": {
    "step": {
      "user": {
        "title": "EZone",
        "description": "Set up your EZone controller",
        "data": {
          "host": "IP Address",
          "port": "Port"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to the EZone controller",
      "invalid_data": "Invalid data received from the controller",
      "unknown": "Unexpected error occurred"
    },
    "abort": {
      "already_configured": "Device is already configured"
    }
  }
}
```

## Installation Steps

1. **Create the directory**: `/config/custom_components/ezone/`

2. **Copy each file** from the artifacts above into this directory

3. **Restart Home Assistant** completely

4. **Add Integration**:
   - Go to Settings → Devices & Services
   - Click "+ Add Integration"  
   - Search for "EZone"
   - Enter IP: `192.168.100.x`
   - Port: `2025`

## Files Needed
You need to copy the content from these artifacts I created earlier:

- `__init__.py` (main integration file)
- `const.py` (constants)
- `config_flow.py` (setup flow)
- `ezone_api.py` (API client)
- `climate.py` (climate entities)
- `cover.py` (damper controls)
- `sensor.py` (temperature sensors)
- `manifest.json` (integration metadata)
- `strings.json` (UI text)

## Quick Setup Script

If you have SSH access, you can run this:

```bash
cd /config
mkdir -p custom_components/ezone
# Then copy each file content into the directory
```

## Troubleshooting

- **Integration doesn't appear**: Check all files are in place and restart HA
- **Connection fails**: Verify IP address and network connectivity  
- **No entities**: Check logs for errors, integration needs to poll first

Your EZone controller at 192.168.100.39:2025 will be automatically discovered once the integration is added.
