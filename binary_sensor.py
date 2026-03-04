"""Binary sensor platform for Fox ESS Charger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


@dataclass
class FoxESSChargerBinarySensorDescription(BinarySensorEntityDescription):
    """Describes Fox ESS Charger binary sensor entity."""

    value_fn: Callable[[dict], bool] | None = None


BINARY_SENSORS: tuple[FoxESSChargerBinarySensorDescription, ...] = (
    FoxESSChargerBinarySensorDescription(
        key="is_charging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-charging",
        value_fn=lambda data: data.get("status") == 3,
    ),
    FoxESSChargerBinarySensorDescription(
        key="vehicle_connected",
        name="Vehicle Connected",
        device_class=BinarySensorDeviceClass.PLUG,
        icon="mdi:power-plug",
        value_fn=lambda data: data.get("cc_status") == 1,
    ),
    FoxESSChargerBinarySensorDescription(
        key="has_fault",
        name="Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle",
        value_fn=lambda data: data.get("fault_code", 0) > 0,
    ),
    FoxESSChargerBinarySensorDescription(
        key="has_alarm",
        name="Alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert",
        value_fn=lambda data: data.get("alarm_code", 0) > 0,
    ),
    FoxESSChargerBinarySensorDescription(
        key="is_locked",
        name="Locked",
        device_class=BinarySensorDeviceClass.LOCK,
        icon="mdi:lock",
        value_fn=lambda data: data.get("lock_status") == 1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fox ESS Charger binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FoxESSChargerBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSORS
    ]

    async_add_entities(entities)


class FoxESSChargerBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Fox ESS Charger binary sensor."""

    entity_description: FoxESSChargerBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: FoxESSChargerBinarySensorDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Fox ESS Charger",
            "manufacturer": "Fox ESS",
            "model": "EV Charger",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
