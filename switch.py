"""Switch entities for FoxESS EV Charger."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, REG_CHARGING_CONTROL, REG_LOCK_CONTROL, REG_AUTO_PHASE_SWITCH
from .__init__ import FoxESSChargerCoordinator
from .modbus_client import FoxESSModbusClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        FoxESSChargingSwitch(d["coordinator"], d["client"], entry),
        FoxESSLockSwitch(d["coordinator"], d["client"], entry),
        FoxESSAutoPhaseSwitchSwitch(d["coordinator"], d["client"], entry),
    ])


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="FoxESS Charger", manufacturer="FoxESS", model="A011",
    )


class FoxESSChargingSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:ev-plug-type2"

    def __init__(self, coordinator: FoxESSChargerCoordinator,
                 client: FoxESSModbusClient, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._client      = client
        self._attr_unique_id   = f"{entry.entry_id}_charging"
        self._attr_name        = "Charging"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        return (self._coordinator.data or {}).get("status") in (2, 3)

    async def async_turn_on(self, **kwargs) -> None:
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_CHARGING_CONTROL, 1
        )
        if success:
            self._coordinator.data["status"] = 3
            self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_CHARGING_CONTROL, 2
        )
        if success:
            self._coordinator.data["status"] = 5
            self.async_write_ha_state()
        await self._coordinator.async_request_refresh()


class FoxESSLockSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:lock"

    def __init__(self, coordinator: FoxESSChargerCoordinator,
                 client: FoxESSModbusClient, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._client      = client
        self._attr_unique_id   = f"{entry.entry_id}_lock"
        self._attr_name        = "Lock"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        # 0x100F: 0 = unlocked, alles andere = locked (Bitmask/Mehrfachwert)
        val = (self._coordinator.data or {}).get("lock_status")
        return val not in (None, 0)

    async def async_turn_on(self, **kwargs) -> None:
        _LOGGER.debug("FoxESS Lock: send Lock (REG_LOCK_CONTROL=2)")
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_LOCK_CONTROL, 2
        )
        if not success:
            _LOGGER.error("FoxESS Lock: Write FAILED")
        # Kein optimistisches Update – echter Wert vom Gerät abwarten
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        _LOGGER.debug("FoxESS Lock: send Unlock (REG_LOCK_CONTROL=1)")
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_LOCK_CONTROL, 1
        )
        if not success:
            _LOGGER.error("FoxESS Lock: Write FAILED")
        # Kein optimistisches Update – echter Wert vom Gerät abwarten
        await self._coordinator.async_request_refresh()


class FoxESSAutoPhaseSwitchSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:auto-fix"

    def __init__(self, coordinator: FoxESSChargerCoordinator,
                 client: FoxESSModbusClient, entry: ConfigEntry) -> None:
        self._coordinator = coordinator
        self._client      = client
        self._attr_unique_id   = f"{entry.entry_id}_auto_phase_switch"
        self._attr_name        = "Auto Phase Switch"
        self._attr_device_info = _device_info(entry)

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        return (self._coordinator.data or {}).get("auto_phase_switch") == 1

    async def async_turn_on(self, **kwargs) -> None:
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_AUTO_PHASE_SWITCH, 1
        )
        if success:
            self._coordinator.data["auto_phase_switch"] = 1
            self.async_write_ha_state()
        await self._coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        success = await self.hass.async_add_executor_job(
            self._client.write_holding_register, REG_AUTO_PHASE_SWITCH, 0
        )
        if success:
            self._coordinator.data["auto_phase_switch"] = 0
            self.async_write_ha_state()
        await self._coordinator.async_request_refresh()