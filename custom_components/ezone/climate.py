class EZoneZoneClimate(CoordinatorEntity, ClimateEntity):
    """EZone zone climate entity."""

    def __init__(self, coordinator, api, zone_num, zone_data):
        """Initialize the zone climate entity."""
        super().__init__(coordinator)
        self._api = api
        self._zone_num = int(zone_num)
        zone_name = self._get_zone_name(zone_num)
        self._attr_name = f"EZone {zone_name}"
        self._attr_unique_id = f"{DOMAIN}_zone_{zone_num}"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = 0  # Zones only control on/off, not temperature

    def _get_zone_name(self, zone_num):
        """Get zone name based on zone number from your YAML config."""
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
        return {
            "identifiers": {(DOMAIN, f"zone_{self._zone_num}")},
            "name": self._attr_name,
            "manufacturer": "EZone",
            "model": "Zone",
            "via_device": (DOMAIN, "main"),
        }

    @property
    def zone_data(self):
        """Return the zone data."""
        return self.coordinator.data.get("zones", {}).get(str(self._zone_num), {})

    @property
    def current_temperature(self):
        """Return the current temperature."""
        # Zones might have temperature sensors in future
        temp_str = self.zone_data.get("actualTemp")
        if temp_str:
            try:
                return float(temp_str)
            except (ValueError, TypeError):
                pass
        return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        # Zones might have individual temperature control in future
        temp_str = self.zone_data.get("desiredTemp")
        if temp_str:
            try:
                return float(temp_str)
            except (ValueError, TypeError):
                pass
        return None

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        # Check if zone is on/off
        zone_setting = self.zone_data.get("setting", "0")
        if zone_setting == "0":
            return HVACMode.OFF
        
        # Get the main system's mode
        system_data = self.coordinator.data.get("system", {})
        unit_control = system_data.get("unitcontrol", {})
        
        if unit_control.get("airconOnOff") == "0":
            return HVACMode.OFF
            
        mode = unit_control.get("mode", "3")
        return EZONE_HVAC_MODES.get(mode, HVACMode.FAN_ONLY)

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.FAN_ONLY]

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._api.async_set_zone_setting(self._zone_num, False)
        else:
            await self._api.async_set_zone_setting(self._zone_num, True)

        await self.coordinator.async_request_refresh()"""Climate platform for EZone integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import EZONE_HVAC_MODES, EZONE_FAN_MODES, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EZone climate entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]

    entities = []

    # Add main aircon unit
    entities.append(EZoneClimate(coordinator, api))

    # Add zones as individual climate entities
    zones_data = coordinator.data.get("zones", {})
    for zone_num, zone_data in zones_data.items():
        entities.append(EZoneZoneClimate(coordinator, api, zone_num, zone_data))

    async_add_entities(entities)


class EZoneClimate(CoordinatorEntity, ClimateEntity):
    """EZone climate entity."""

    def __init__(self, coordinator, api):
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "EZone Aircon"
        self._attr_unique_id = f"{DOMAIN}_main"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "main")},
            "name": self._attr_name,
            "manufacturer": "EZone",
            "model": "e-zone",
        }

    @property
    def system_data(self):
        """Return the system data."""
        return self.coordinator.data.get("system", {})

    @property
    def unit_control(self):
        """Return the unit control data."""
        return self.system_data.get("unitcontrol", {})

    @property
    def current_temperature(self):
        """Return the current temperature."""
        temp_str = self.unit_control.get("centralActualTemp", "0")
        try:
            return float(temp_str)
        except (ValueError, TypeError):
            return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        temp_str = self.unit_control.get("centralDesiredTemp", "24")
        try:
            return float(temp_str)
        except (ValueError, TypeError):
            return 24.0

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        if self.unit_control.get("airconOnOff") == "0":
            return HVACMode.OFF
        
        mode = self.unit_control.get("mode", "3")
        return EZONE_HVAC_MODES.get(mode, HVACMode.FAN_ONLY)

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        modes = [HVACMode.OFF]
        modes.extend(EZONE_HVAC_MODES.values())
        return modes

    @property
    def fan_mode(self):
        """Return the current fan mode."""
        fan_speed = self.unit_control.get("fanSpeed", "2")
        return EZONE_FAN_MODES.get(fan_speed, "medium")

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return list(EZONE_FAN_MODES.values())

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self._api.async_set_target_temp(temperature)
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._api.async_set_aircon_on_off(False)
        else:
            # Find the EZone mode for this HVAC mode
            ezone_mode = None
            for mode_num, ha_mode in EZONE_HVAC_MODES.items():
                if ha_mode == hvac_mode:
                    ezone_mode = int(mode_num)
                    break
            
            if ezone_mode:
                await self._api.async_set_aircon_on_off(True)
                await self._api.async_set_mode(ezone_mode)

        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        # Find the EZone fan speed
        ezone_speed = None
        for speed_num, ha_fan in EZONE_FAN_MODES.items():
            if ha_fan == fan_mode:
                ezone_speed = int(speed_num)
                break
        
        if ezone_speed:
            await self._api.async_set_fan_speed(ezone_speed)
            await self.coordinator.async_request_refresh()


class EZoneZoneClimate(CoordinatorEntity, ClimateEntity):
    """EZone zone climate entity."""

    def __init__(self, coordinator, api, ac_key, zone_key, zone_data):
        """Initialize the zone climate entity."""
        super().__init__(coordinator)
        self._api = api
        self._ac_key = ac_key
        self._zone_key = zone_key
        self._attr_name = zone_data.get("name", f"Zone {zone_key}")
        self._attr_unique_id = f"{DOMAIN}_{ac_key}_zone_{zone_key}"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"{self._ac_key}_zone_{self._zone_key}")},
            "name": self._attr_name,
            "manufacturer": "EZone",
            "model": "Zone",
            "via_device": (DOMAIN, self._ac_key),
        }

    @property
    def zone_data(self):
        """Return the zone data."""
        return (
            self.coordinator.data.get("aircons", {})
            .get(self._ac_key, {})
            .get("zones", {})
            .get(self._zone_key, {})
        )

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.zone_data.get("temp")

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self.zone_data.get("setTemp")

    @property
    def hvac_mode(self):
        """Return the current HVAC mode."""
        # Zone follows the main AC unit's mode but can be turned off individually
        if self.zone_data.get("state") == "close":
            return HVACMode.OFF
        
        # Get the main AC's mode
        ac_info = (
            self.coordinator.data.get("aircons", {})
            .get(self._ac_key, {})
            .get("info", {})
        )
        
        if ac_info.get("state") == "off":
            return HVACMode.OFF
            
        mode = ac_info.get("mode")
        return EZONE_HVAC_MODES.get(mode, HVACMode.OFF)

    @property
    def hvac_modes(self):
        """Return the list of available HVAC modes."""
        return [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.FAN_ONLY, HVACMode.DRY]

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        await self._api.aircon.async_update_zone(
            self._ac_key, self._zone_key, {"setTemp": int(temperature)}
        )
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._api.aircon.async_update_zone(
                self._ac_key, self._zone_key, {"state": "close"}
            )
        else:
            await self._api.aircon.async_update_zone(
                self._ac_key, self._zone_key, {"state": "open"}
            )

        await self.coordinator.async_request_refresh()
