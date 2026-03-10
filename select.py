"""Select entities for FoxESS EV Charger."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, REG_WORK_MODE, REG_PHASE_SWITCHING, WORK_MODE_MAP, PHASE_SEQ_MAP
from .__init__ import FoxESSChargerCoordinator
from .modbus_client import FoxESSModbusClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        FoxESSWorkModeSelect(d["coordinator"], d["client"], entry),
        FoxESSPhaseSelect(d["coordinator"], d["client"], entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="FoxESS Charger", manufacturer="FoxESS", model="A011",
    )


class FoxESSWorkModeSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:ev-station"
    _options_map = WORK_MODE_MAP
    _reverse_map = {v: k for k, v in WORK_MODE_MAP.items()}

    def __init__(self, coordinator: FoxESSChargerCoordinator,
                 client: FoxESSModbusClient, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._client      = client
        self._attr_unique_id   = f"{entry.entry_id}_work_mode"
        self._attr_name        = "Work Mode"
        self._attr_options     = list(self._options_map.values())
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def current_option(self) -> str | None:
        raw = self._coordinator.data.get("work_mode") if self._coordinator.data else None
        return self._options_map.get(raw) if raw is not None else None

    async def async_select_option(self, option: str) -> None:
        value = self._reverse_map[option]
        _LOGGER.debug("FoxESS: write work_mode=%s (%d) → 0x%04X", option, value, REG_WORK_MODE)
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_WORK_MODE, value  # ← REG_WORK_MODE (FC 0x10)
        )
        if success:
            self._coordinator.data["work_mode"] = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("FoxESS: Work Mode write FAILED for option=%s", option)
        await self._coordinator.async_request_refresh()


class FoxESSPhaseSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:electric-switch"
    _options_map = PHASE_SEQ_MAP
    _reverse_map = {v: k for k, v in PHASE_SEQ_MAP.items()}

    def __init__(self, coordinator: FoxESSChargerCoordinator,
                 client: FoxESSModbusClient, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._client      = client
        self._attr_unique_id   = f"{entry.entry_id}_phase_sequence"
        self._attr_name        = "Phase Sequence"
        self._attr_options     = list(self._options_map.values())
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def current_option(self) -> str | None:
        raw = self._coordinator.data.get("phase_sequence") if self._coordinator.data else None
        return self._options_map.get(raw) if raw is not None else None

    async def async_select_option(self, option: str) -> None:
        value = self._reverse_map[option]
        _LOGGER.debug("FoxESS: write phase=%s (%d) → 0x%04X", option, value, REG_PHASE_SWITCHING)
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_PHASE_SWITCHING, value  # ← FC 0x06 (W-Only)
        )
        if success:
            self._coordinator.data["phase_sequence"] = value
            self.async_write_ha_state()
        else:
            _LOGGER.error("FoxESS: Phase Sequence write FAILED")
        await self._coordinator.async_request_refresh()