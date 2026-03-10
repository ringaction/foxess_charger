"""Binary sensors for FoxESS EV Charger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .__init__ import FoxESSChargerCoordinator


@dataclass(frozen=True, kw_only=True)
class FoxESSBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict], bool] = lambda _: False


BINARY_SENSORS: tuple[FoxESSBinarySensorDescription, ...] = (
    FoxESSBinarySensorDescription(
        key="is_charging", name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        icon="mdi:battery-charging",
        value_fn=lambda d: d.get("status") == 3,
    ),
    FoxESSBinarySensorDescription(
        key="vehicle_connected", name="Vehicle Connected",
        device_class=BinarySensorDeviceClass.PLUG, icon="mdi:power-plug",
        value_fn=lambda d: d.get("cc_status") == 1,
    ),
    FoxESSBinarySensorDescription(
        key="has_fault", name="Fault",
        device_class=BinarySensorDeviceClass.PROBLEM, icon="mdi:alert-circle",
        value_fn=lambda d: d.get("fault_code", 0) > 0,
    ),
    FoxESSBinarySensorDescription(
        key="has_alarm", name="Alarm",
        device_class=BinarySensorDeviceClass.PROBLEM, icon="mdi:alert",
        value_fn=lambda d: d.get("alarm_code", 0) > 0,
    ),
    FoxESSBinarySensorDescription(
        key="is_locked", name="Locked",
        device_class=BinarySensorDeviceClass.LOCK, icon="mdi:lock",
        value_fn=lambda d: d.get("lock_status") == 1,
    ),
    FoxESSBinarySensorDescription(
        key="auto_phase_switch", name="Auto Phase Switch",
        icon="mdi:auto-fix",
        value_fn=lambda d: d.get("auto_phase_switch") == 1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FoxESSChargerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        FoxESSBinarySensor(coordinator, desc, entry) for desc in BINARY_SENSORS
    ])


class FoxESSBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True
    entity_description: FoxESSBinarySensorDescription

    def __init__(self, coordinator: FoxESSChargerCoordinator,
                 description: FoxESSBinarySensorDescription, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="FoxESS Charger", manufacturer="FoxESS", model="A011",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.entity_description.value_fn(self.coordinator.data)
        return None
