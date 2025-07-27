"""Sensor platform for EZone integration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EZone sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []

    # Add main system temperature sensors
    entities.append(EZoneTemperatureSensor(coordinator, "current"))
    entities.append(EZoneTemperatureSensor(coordinator, "target"))
    
    # Add zone sensors if they have temperature data
    zones_data = coordinator.data.get("zones", {})
    for zone_num, zone_data in zones_data.items():
        if zone_data.get("actualTemp"):
            entities.append(EZoneZoneTemperatureSensor(coordinator, zone_num, zone_data))

    async_add_entities(entities)


class EZoneTemperatureSensor(CoordinatorEntity, SensorEntity):
    """EZone temperature sensor."""

    def __init__(self, coordinator, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._attr_name = f"EZone {sensor_type.title()} Temperature"
        self._attr_unique_id = f"{DOMAIN}_{sensor_type}_temp"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, "main")},
            "name": "EZone Aircon",
            "manufacturer": "EZone",
            "model": "e-zone",
        }

    @property
    def native_value(self):
        """Return the sensor value."""
        system_data = self.coordinator.data.get("system", {})
        unit_control = system_data.get("unitcontrol", {})
        
        if self._sensor_type == "current":
            temp_str = unit_control.get("centralActualTemp", "0")
        elif self._sensor_type == "target":
            temp_str = unit_control.get("centralDesiredTemp", "24")
        else:
            return None
            
        try:
            return float(temp_str)
        except (ValueError, TypeError):
            return None


class EZoneZoneTemperatureSensor(CoordinatorEntity, SensorEntity):
    """EZone zone temperature sensor.""" temperature sensor."""

    def __init__(self, coordinator, ac_key, zone_key, zone_data):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ac_key = ac_key
        self._zone_key = zone_key
        self._attr_name = f"{zone_data.get('name', f'Zone {zone_key}')} Temperature"
        self._attr_unique_id = f"{DOMAIN}_{ac_key}_zone_{zone_key}_temp"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"{self._ac_key}_zone_{self._zone_key}")},
            "name": self.zone_data.get("name", f"Zone {self._zone_key}"),
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
    def native_value(self):
        """Return the sensor value."""
        return self.zone_data.get("temp")


class EZoneZonePositionSensor(CoordinatorEntity, SensorEntity):
    """EZone zone damper position sensor."""

    def __init__(self, coordinator, ac_key, zone_key, zone_data):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ac_key = ac_key
        self._zone_key = zone_key
        self._attr_name = f"{zone_data.get('name', f'Zone {zone_key}')} Damper Position"
        self._attr_unique_id = f"{DOMAIN}_{ac_key}_zone_{zone_key}_position"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"{self._ac_key}_zone_{self._zone_key}")},
            "name": self.zone_data.get("name", f"Zone {self._zone_key}"),
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
    def native_value(self):
        """Return the sensor value."""
        return self.zone_data.get("value", 0)
