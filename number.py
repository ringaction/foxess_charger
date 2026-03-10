"""Number entities for FoxESS EV Charger."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfPower, UnitOfTime, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    REG_MAX_CHARGING_CURRENT, REG_MAX_CHARGING_POWER,
    REG_ALLOWED_CHARGE_TIME,  REG_ALLOWED_CHARGE_ENERGY,
    REG_TIME_VALIDITY,        REG_DEFAULT_CURRENT,
    REG_MIN_SWITCH_INTERVAL,
)
from .__init__ import FoxESSChargerCoordinator
from .modbus_client import FoxESSModbusClient

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class FoxESSNumberDescription(NumberEntityDescription):
    register:     int                     = 0
    data_key:     str                     = ""
    scale_to_raw: Callable[[float], int]  = lambda v: int(v)
    scale_to_ha:  Callable[[int], float]  = lambda v: float(v)


NUMBERS: tuple[FoxESSNumberDescription, ...] = (
    FoxESSNumberDescription(
        key="max_charging_current", name="Max Charging Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6.0, native_max_value=32.0, native_step=0.1,
        register=REG_MAX_CHARGING_CURRENT, data_key="max_charging_current_raw",
        scale_to_raw=lambda v: int(round(v * 10)),
        scale_to_ha =lambda v: round(v * 0.1, 1),
    ),
    FoxESSNumberDescription(
        key="max_charging_power", name="Max Charging Power",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        native_min_value=0.0, native_max_value=22.0, native_step=0.1,
        register=REG_MAX_CHARGING_POWER, data_key="max_charging_power_raw",
        scale_to_raw=lambda v: int(round(v * 10)),
        scale_to_ha =lambda v: round(v * 0.1, 1),
    ),
    FoxESSNumberDescription(
        key="allowed_charge_time", name="Allowed Charge Time",
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=0, native_max_value=1440, native_step=1,
        register=REG_ALLOWED_CHARGE_TIME, data_key="allowed_charge_time",
    ),
    FoxESSNumberDescription(
        key="allowed_charge_energy", name="Allowed Charge Energy",
        icon="mdi:battery-charging",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        native_min_value=0, native_max_value=999, native_step=1,
        register=REG_ALLOWED_CHARGE_ENERGY, data_key="allowed_charge_energy",
    ),
    FoxESSNumberDescription(
        key="time_validity", name="Command Time Validity",
        icon="mdi:clock-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=10, native_max_value=60, native_step=1,
        register=REG_TIME_VALIDITY, data_key="time_validity",
    ),
    FoxESSNumberDescription(
        key="default_current", name="Default Current (Fallback)",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        native_min_value=6.0, native_max_value=32.0, native_step=0.1,
        register=REG_DEFAULT_CURRENT, data_key="default_current_raw",
        scale_to_raw=lambda v: int(round(v * 10)),
        scale_to_ha =lambda v: round(v * 0.1, 1),
    ),
    FoxESSNumberDescription(
        key="min_switch_interval", name="Min Phase Switch Interval",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=5, native_max_value=30, native_step=1,
        register=REG_MIN_SWITCH_INTERVAL, data_key="min_switch_interval",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        FoxESSNumber(d["coordinator"], d["client"], desc, entry) for desc in NUMBERS
    ])


class FoxESSNumber(NumberEntity):
    _attr_has_entity_name = True
    entity_description: FoxESSNumberDescription

    def __init__(
        self,
        coordinator: FoxESSChargerCoordinator,
        client: FoxESSModbusClient,
        description: FoxESSNumberDescription,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._client      = client
        self.entity_description = description
        self._attr_unique_id   = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="FoxESS Charger",
            manufacturer="FoxESS",
            model="A011",
        )  # ← diese schließende Klammer fehlte

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def native_value(self) -> float | None:
        raw = (self._coordinator.data or {}).get(self.entity_description.data_key)
        if raw is None:
            return None
        return self.entity_description.scale_to_ha(raw)

    async def async_set_native_value(self, value: float) -> None:
        desc = self.entity_description
        raw  = desc.scale_to_raw(value)
        _LOGGER.debug(
            "FoxESS: write %s=%s (raw=%d) → 0x%04X",
            desc.key, value, raw, desc.register,
        )
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, desc.register, raw
        )
        if success:
            self._coordinator.data[desc.data_key] = raw
            self.async_write_ha_state()
        else:
            _LOGGER.error("FoxESS: Write failed for %s", desc.key)
        await self._coordinator.async_request_refresh()