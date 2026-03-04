from __future__ import annotations

from typing import Final

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import FoxESSChargerDataUpdateCoordinator
from .modbus_client import FoxESSModbusClient


CHARGING_CONTROL_REGISTER: Final[int] = 0x4001  # W: 0=No action,1=Start,2=Stop
STATUS_REGISTER: Final[int] = 0x1003  # Input, 3=charging,5=finish,6=fault


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FoxESSChargerDataUpdateCoordinator = data["coordinator"]
    client: FoxESSModbusClient = data["client"]

    entities: list[SwitchEntity] = [
        FoxESSChargingSwitch(coordinator, client, entry),
    ]

    async_add_entities(entities)


class FoxESSChargingSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:ev-plug-type2"

    def __init__(
        self,
        coordinator: FoxESSChargerDataUpdateCoordinator,
        client: FoxESSModbusClient,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._client = client
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_charging_switch"
        self._attr_name = "Charging"

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
    def is_on(self) -> bool:
        """
        EVC Status Register (0x1003):
        3=charging, 2=start → als „an“ interpretieren.
        """
        status = self._coordinator.data.get("input_registers", {}).get(STATUS_REGISTER)
        if status is None:
            return False
        return status in (2, 3)

    async def async_turn_on(self, **kwargs: object) -> None:
        LOGGER.debug(
            "FoxESS Charger: sending START (1) to 0x%04X", CHARGING_CONTROL_REGISTER
        )
        await self.hass.async_add_executor_job(
            self._client.write_holding_register,
            CHARGING_CONTROL_REGISTER,
            1,
        )

        # Optimistischer State bis zum nächsten Poll
        self._coordinator.data.setdefault("input_registers", {})[STATUS_REGISTER] = 3
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        LOGGER.debug(
            "FoxESS Charger: sending STOP (2) to 0x%04X", CHARGING_CONTROL_REGISTER
        )
        await self.hass.async_add_executor_job(
            self._client.write_holding_register,
            CHARGING_CONTROL_REGISTER,
            2,
        )

        self._coordinator.data.setdefault("input_registers", {})[STATUS_REGISTER] = 5
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()
