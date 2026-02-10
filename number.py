"""Number platform for Fox ESS Charger."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_MAX_CHARGING_CURRENT,
    REG_MAX_CHARGING_POWER,
    REG_ALLOWED_CHARGE_TIME,
    REG_ALLOWED_CHARGE_ENERGY,
    REG_DEFAULT_CURRENT,
    REG_TIME_VALIDITY,
    REG_MIN_SWITCH_INTERVAL,
)


@dataclass
class FoxESSChargerNumberDescription(NumberEntityDescription):
    """Describes Fox ESS Charger number entity."""

    register: int | None = None
    scale: float = 1.0


NUMBERS: tuple[FoxESSChargerNumberDescription, ...] = (
    FoxESSChargerNumberDescription(
        key="max_charging_current",
        name="Max Charging Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6,
        native_max_value=32,
        native_step=0.1,
        register=REG_MAX_CHARGING_CURRENT,
        scale=10.0,  # Value * 10 for register
    ),
    FoxESSChargerNumberDescription(
        key="max_charging_power",
        name="Max Charging Power",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        native_min_value=1.4,
        native_max_value=22,
        native_step=0.1,
        register=REG_MAX_CHARGING_POWER,
        scale=10.0,
    ),
    FoxESSChargerNumberDescription(
        key="allowed_charge_time",
        name="Allowed Charge Time",
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=0,
        native_max_value=1440,
        native_step=1,
        register=REG_ALLOWED_CHARGE_TIME,
        scale=1.0,
    ),
    FoxESSChargerNumberDescription(
        key="allowed_charge_energy",
        name="Allowed Charge Energy",
        icon="mdi:battery-charging",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        register=REG_ALLOWED_CHARGE_ENERGY,
        scale=1.0,
    ),
    FoxESSChargerNumberDescription(
        key="default_current",
        name="Default Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6,
        native_max_value=32,
        native_step=0.1,
        register=REG_DEFAULT_CURRENT,
        scale=10.0,
    ),
    FoxESSChargerNumberDescription(
        key="time_validity",
        name="Time Validity",
        icon="mdi:clock-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=10,
        native_max_value=60,
        native_step=1,
        register=REG_TIME_VALIDITY,
        scale=1.0,
    ),
    FoxESSChargerNumberDescription(
        key="min_switch_interval",
        name="Min Switch Interval",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=5,
        native_max_value=30,
        native_step=1,
        register=REG_MIN_SWITCH_INTERVAL,
        scale=1.0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fox ESS Charger number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FoxESSChargerNumber(coordinator, description, entry) for description in NUMBERS
    ]

    async_add_entities(entities)


class FoxESSChargerNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Fox ESS Charger number entity."""

    entity_description: FoxESSChargerNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: FoxESSChargerNumberDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
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
    def native_value(self) -> float | None:
        """Return the value of the number."""
        if self.coordinator.data:
            key_with_raw = f"{self.entity_description.key}_raw"
            raw_value = self.coordinator.data.get(key_with_raw)
            if raw_value is not None:
                return round(raw_value / self.entity_description.scale, 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        register_value = int(value * self.entity_description.scale)
        success = await self.hass.async_add_executor_job(
            self.coordinator.write_register,
            self.entity_description.register,
            register_value,
        )
        if success:
            await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
