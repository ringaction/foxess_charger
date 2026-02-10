"""Switch platform for Fox ESS Charger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_CHARGING_CONTROL,
    REG_LOCK_CONTROL,
)


@dataclass
class FoxESSChargerSwitchDescription(SwitchEntityDescription):
    """Describes Fox ESS Charger switch entity."""

    register: int | None = None
    on_value: int = 1
    off_value: int = 2


SWITCHES: tuple[FoxESSChargerSwitchDescription, ...] = (
    FoxESSChargerSwitchDescription(
        key="charging",
        name="Charging",
        icon="mdi:ev-station",
        register=REG_CHARGING_CONTROL,
        on_value=1,  # Start charging
        off_value=2,  # Stop charging
    ),
    FoxESSChargerSwitchDescription(
        key="lock",
        name="Lock",
        icon="mdi:lock",
        register=REG_LOCK_CONTROL,
        on_value=2,  # Lock
        off_value=1,  # Unlock
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fox ESS Charger switch entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FoxESSChargerSwitch(coordinator, description, entry) for description in SWITCHES
    ]

    async_add_entities(entities)


class FoxESSChargerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Fox ESS Charger switch."""

    entity_description: FoxESSChargerSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: FoxESSChargerSwitchDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
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
        """Return true if the switch is on."""
        if self.coordinator.data:
            if self.entity_description.key == "charging":
                # Charging switch is "on" when status is 3 (charging)
                return self.coordinator.data.get("status") == 3
            elif self.entity_description.key == "lock":
                # Lock switch is "on" when lock_status is 1 (locked)
                return self.coordinator.data.get("lock_status") == 1
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.write_register,
            self.entity_description.register,
            self.entity_description.on_value,
        )
        if success:
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        success = await self.hass.async_add_executor_job(
            self.coordinator.write_register,
            self.entity_description.register,
            self.entity_description.off_value,
        )
        if success:
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
