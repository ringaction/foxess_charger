from __future__ import annotations

from typing import Final

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import FoxESSChargerDataUpdateCoordinator
from .modbus_client import FoxESSModbusClient


MAX_CURRENT_REGISTER: Final[int] = 0x3001  # R/W, 0.1 A resolution


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FoxESSChargerDataUpdateCoordinator = data["coordinator"]
    client: FoxESSModbusClient = data["client"]

    entities: list[NumberEntity] = [
        FoxESSMaxCurrentNumber(coordinator, client, entry),
    ]

    async_add_entities(entities)


class FoxESSMaxCurrentNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:current-ac"
    _attr_unit_of_measurement = "A"
    _attr_native_min_value = 6.0
    _attr_native_max_value = 32.0
    _attr_native_step = 0.1

    def __init__(
        self,
        coordinator: FoxESSChargerDataUpdateCoordinator,
        client: FoxESSModbusClient,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._client = client
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_max_current"
        self._attr_name = "Max Charging Current"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="FoxESS Charger",
            manufacturer="FoxESS",
            model="A011",
        )

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def native_value(self) -> float | None:
        raw = self._coordinator.data.get("holding_registers", {}).get(
            MAX_CURRENT_REGISTER
        )
        if raw is None:
            return None
        # Register 0x3001: 0.1 A → A
        return raw / 10.0

    async def async_set_native_value(self, value: float) -> None:
        # Begrenzen im zulässigen Bereich
        if value < self._attr_native_min_value:
            value = self._attr_native_min_value
        if value > self._attr_native_max_value:
            value = self._attr_native_max_value

        raw = int(round(value * 10))  # A → 0.1 A
        LOGGER.debug(
            "FoxESS Charger: setting max current to %s A (raw=%s) on 0x%04X",
            value,
            raw,
            MAX_CURRENT_REGISTER,
        )

        await self.hass.async_add_executor_job(
            self._client.write_holding_register,
            MAX_CURRENT_REGISTER,
            raw,
        )

        self._coordinator.data.setdefault("holding_registers", {})[
            MAX_CURRENT_REGISTER
        ] = raw
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()
