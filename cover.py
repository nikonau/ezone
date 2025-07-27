"""Cover platform for EZone integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import CoverEntity, CoverEntityFeature, CoverDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ZONE_OPEN, ZONE_CLOSE

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EZone cover entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []

    # Add zone dampers as cover entities
    zones_data = coordinator.data.get("zones", {})
    for zone_num, zone_data in zones_data.items():
        entities.append(EZoneZoneCover(coordinator, api, zone_num, zone_data))

    async_add_entities(entities)


class EZoneZoneCover(CoordinatorEntity, CoverEntity):
    """EZone zone damper cover entity."""

    def __init__(self, coordinator, api, zone_num, zone_data):
        """Initialize the cover entity."""
        super().__init__(coordinator)
        self._api = api
        self._zone_num = int(zone_num)
        zone_name = self._get_zone_name(zone_num)
        self._attr_name = f"EZone {zone_name} Damper"
        self._attr_unique_id = f"{DOMAIN}_zone_{zone_num}_damper"
        self._attr_device_class = CoverDeviceClass.DAMPER
        self._attr_supported_features = (
            CoverEntityFeature.OPEN 
            | CoverEntityFeature.CLOSE 
            | CoverEntityFeature.SET_POSITION
        )

    def _get_zone_name(self, zone_num):
        """Get zone name based on zone number."""
        zone_names = {
            "1": "Living",
            "2": "Theatre", 
            "3": "Master Bed",
            "4": "Bed 2",
            "5": "Bed 3"
        }
        return zone_names.get(str(zone_num), f"Zone {zone_num}")

    @property
    def device_info(self):
        """Return device information."""
        zone_name = self._get_zone_name(self._zone_num)
        return {
            "identifiers": {(DOMAIN, f"zone_{self._zone_num}")},
            "name": f"EZone {zone_name}",
            "manufacturer": "EZone",
            "model": "Zone Damper",
            "via_device": (DOMAIN, "main"),
        }

    @property
    def zone_data(self):
        """Return the zone data."""
        return self.coordinator.data.get("zones", {}).get(str(self._zone_num), {})

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        # Get percentage setting if available
        percent_str = self.zone_data.get("userPercentSetting", "0")
        try:
            return int(percent_str)
        except (ValueError, TypeError):
            # Fallback to basic open/close
            setting = self.zone_data.get("setting", "0")
            return 100 if setting == "1" else 0

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        setting = self.zone_data.get("setting", "0")
        return setting == "0"

    @property
    def is_open(self):
        """Return if the cover is open."""
        setting = self.zone_data.get("setting", "0")
        return setting == "1"

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        await self._api.async_set_zone_setting(self._zone_num, True)
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        await self._api.async_set_zone_setting(self._zone_num, False)
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get("position")
        if position is None:
            return

        if position == 0:
            await self._api.async_set_zone_setting(self._zone_num, False)
        else:
            await self._api.async_set_zone_percent(self._zone_num, position)
        
        await self.coordinator.async_request_refresh()