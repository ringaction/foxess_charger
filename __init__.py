"""FoxESS EV Charger integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, PLATFORMS,
    CONF_HOST, CONF_PORT, CONF_SLAVE_ID,
    DEFAULT_SCAN_INTERVAL,
)
from .modbus_client import FoxESSModbusClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    host      = entry.data[CONF_HOST]
    port      = entry.data[CONF_PORT]
    slave_id  = entry.data[CONF_SLAVE_ID]
    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)

    client      = FoxESSModbusClient(host, port, slave_id)
    coordinator = FoxESSChargerCoordinator(hass, client, scan_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client":      client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(data["client"].disconnect)
    return unload_ok


class FoxESSChargerCoordinator(DataUpdateCoordinator):
    """Coordinator: pollt alle Modbus-Register des Chargers."""

    def __init__(self, hass: HomeAssistant, client: FoxESSModbusClient,
                 scan_interval: int) -> None:
        self.client = client
        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        try:
            return await self.hass.async_add_executor_job(self._fetch)
        except Exception as err:
            raise UpdateFailed(f"Modbus error: {err}") from err

    def _fetch(self) -> dict:
        data: dict = {}

        # ── 0x1000–0x1015: 22 Status-Register ────────────────────────────────
        regs = self.client.read_registers(0x1000, 22)
        if regs and len(regs) >= 22:
            data["device_address"]  = regs[0]
            data["software_version"]= regs[1]
            data["stop_reason"]     = regs[2]
            data["status"]          = regs[3]
            data["cp_status"]       = regs[4]
            data["cc_status"]       = regs[5]
            data["port_temp_raw"]   = regs[6]
            data["ambient_temp_raw"]= regs[7]
            data["l1_voltage_raw"]  = regs[8]
            data["l2_voltage_raw"]  = regs[9]
            data["l3_voltage_raw"]  = regs[10]
            data["l1_current_raw"]  = regs[11]
            data["l2_current_raw"]  = regs[12]
            data["l3_current_raw"]  = regs[13]
            data["power_raw"]       = regs[14]
            data["lock_status"]     = regs[15]
            data["phase_sequence"]  = regs[16]
            data["max_power_raw"]   = regs[17]
            data["min_power_raw"]   = regs[18]
            data["max_current_raw"] = regs[19]
            data["min_current_raw"] = regs[20]
            data["alarm_code"]      = regs[21]
        else:
            _LOGGER.warning("Could not read status registers 0x1000–0x1015")

        # ── 0x1016/0x1018/0x101A/0x101C: UINT32 Register ─────────────────────
        for key, addr in [
            ("current_energy_raw", 0x1016),
            ("total_energy_raw",   0x1018),
            ("fault_code",         0x101A),
            ("rfid_card",          0x101C),
        ]:
            val = self.client.read_uint32(addr)
            if val is not None:
                data[key] = val

        # ── 0x3000–0x300B: R/W Config Register ───────────────────────────────
        cfg = self.client.read_registers(0x3000, 12)
        if cfg and len(cfg) >= 12:
            data["work_mode"]                = cfg[0]
            data["max_charging_current_raw"] = cfg[1]
            data["max_charging_power_raw"]   = cfg[2]
            data["allowed_charge_time"]      = cfg[3]
            data["allowed_charge_energy"]    = cfg[4]
            data["time_validity"]            = cfg[5]
            data["default_current_raw"]      = cfg[6]
            # cfg[7..9] reserviert
            data["auto_phase_switch"]        = cfg[10]
            data["min_switch_interval"]      = cfg[11]
        else:
            _LOGGER.warning("Could not read config registers 0x3000–0x300B")

        return data
