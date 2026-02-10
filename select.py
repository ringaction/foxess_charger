"""Select platform for Fox ESS Charger."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_WORK_MODE,
    REG_AUTO_PHASE_SWITCH,
    REG_PHASE_SWITCHING,
    WORK_MODE_MAP,
    PHASE_SEQUENCE_MAP,
)


@dataclass
class FoxESSChargerSelectDescription(SelectEntityDescription):
    """Describes Fox ESS Charger select entity."""

    register: int | None = None
    value_map: dict[str, int] | None = None


SELECTS: tuple[FoxESSChargerSelectDescription, ...] = (
    FoxESSChargerSelectDescription(
        key="work_mode_control",
        name="Work Mode",
        icon="mdi:cog",
        options=["controlled", "plug_and_charge", "locked"],
        register=REG_WORK_MODE,
        value_map={"controlled": 0, "plug_and_charge": 1, "locked": 2},
    ),
    FoxESSChargerSelectDescription(
        key="auto_phase_switch_control",
        name="Auto Phase Switch",
        icon="mdi:auto-mode",
        options=["disabled", "enabled"],
        register=REG_AUTO_PHASE_SWITCH,
        value_map={"disabled": 0, "enabled": 1},
    ),
    FoxESSChargerSelectDescription(
        key="phase_switching_control",
        name="Phase Switching",
        icon="mdi:electric-switch",
        options=["three_phase", "l2_single_phase", "l3_single_phase"],
        register=REG_PHASE_SWITCHING,
        value_map={"three_phase": 0, "l2_single_phase": 1, "l3_single_phase": 2},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fox ESS Charger select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FoxESSChargerSelect(coordinator, description, entry) for description in SELECTS
    ]

    async_add_entities(entities)


class FoxESSChargerSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Fox ESS Charger select entity."""

    entity_description: FoxESSChargerSelectDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: FoxESSChargerSelectDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select entity."""
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
    def current_option(self) -> str | None:
        """Return the current option."""
        if self.coordinator.data and self.entity_description.value_map:
            # Get the base key without _control suffix
            base_key = self.entity_description.key.replace("_control", "")
            value = self.coordinator.data.get(base_key)
            
            if value is not None:
                # Reverse lookup in value_map
                for option, val in self.entity_description.value_map.items():
                    if val == value:
                        return option
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self.entity_description.value_map and option in self.entity_description.value_map:
            value = self.entity_description.value_map[option]
            success = await self.hass.async_add_executor_job(
                self.coordinator.write_register,
                self.entity_description.register,
                value,
            )
            if success:
                await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
