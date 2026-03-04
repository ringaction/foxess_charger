from __future__ import annotations

from typing import Any, Final

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import FoxESSChargerDataUpdateCoordinator
from .modbus_client import FoxESSModbusClient


WORK_MODE_REGISTER: Final[int] = 0x3000  # R/W, 0=Controlled,1=Plug&Charge,2=Locked


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: FoxESSChargerDataUpdateCoordinator = data["coordinator"]
    client: FoxESSModbusClient = data["client"]

    entities: list[SelectEntity] = [
        FoxESSWorkModeSelect(coordinator, client, entry),
    ]

    async_add_entities(entities)


class FoxESSWorkModeSelect(SelectEntity):
    _attr_has_entity_name = True

    _options_map: dict[int, str] = {
        0: "Controlled",
        1: "Plug&Charge",
        2: "Locked",
    }
    _reverse_map: dict[str, int] = {v: k for k, v in _options_map.items()}

    def __init__(
        self,
        coordinator: FoxESSChargerDataUpdateCoordinator,
        client: FoxESSModbusClient,
        entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._client = client
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_work_mode"
        self._attr_name = "Work Mode"
        self._attr_icon = "mdi:ev-station"
        self._attr_options = list(self._options_map.values())

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
    def current_option(self) -> str | None:
        # coordinator.data["holding_registers"] ist ein dict {register: value}
        raw = self._coordinator.data.get("holding_registers", {}).get(WORK_MODE_REGISTER)
        if raw is None:
            return None
        return self._options_map.get(raw)

    async def async_select_option(self, option: str) -> None:
        if option not in self._reverse_map:
            raise ValueError(f"Unsupported work mode option: {option}")

        value = self._reverse_map[option]
        LOGGER.debug(
            "FoxESS Charger: setting work mode to %s (%s) on 0x%04X",
            option,
            value,
            WORK_MODE_REGISTER,
        )

        await self.hass.async_add_executor_job(
            self._client.write_holding_register,
            WORK_MODE_REGISTER,
            value,
        )

        # Cache aktualisieren, bis der nächste Poll kommt
        self._coordinator.data.setdefault("holding_registers", {})[
            WORK_MODE_REGISTER
        ] = value
        self.async_write_ha_state()
        await self._coordinator.async_request_refresh()
