"""The Fox ESS Charger integration."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_SLAVE_ID,
    DEFAULT_SCAN_INTERVAL,
)
from .modbus_client import FoxESSModbusClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fox ESS Charger from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    slave_id = entry.data[CONF_SLAVE_ID]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create modbus client
    modbus_client = FoxESSModbusClient(host, port, slave_id)

    # Create coordinator
    coordinator = FoxESSChargerCoordinator(
        hass, modbus_client, scan_interval
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Disconnect modbus client
        await hass.async_add_executor_job(coordinator.modbus_client.disconnect)

    return unload_ok


class FoxESSChargerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Fox ESS Charger data."""

    def __init__(
        self,
        hass: HomeAssistant,
        modbus_client: FoxESSModbusClient,
        scan_interval: int,
    ) -> None:
        """Initialize."""
        self.modbus_client = modbus_client

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from the device."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    def _fetch_data(self) -> dict:
        """Fetch all data from Modbus registers."""
        data = {}

        try:
            # Read basic status registers (0x1000-0x1015) - 22 registers
            basic_data = self.modbus_client.read_holding_registers(0x1000, 22)
            if basic_data and len(basic_data) >= 22:
                data["device_address"] = basic_data[0]
                data["software_version"] = basic_data[1]
                data["stop_reason"] = basic_data[2]
                data["status"] = basic_data[3]
                data["cp_status"] = basic_data[4]
                data["cc_status"] = basic_data[5]
                data["port_temp_raw"] = basic_data[6]
                data["ambient_temp_raw"] = basic_data[7]
                data["l1_voltage_raw"] = basic_data[8]
                data["l2_voltage_raw"] = basic_data[9]
                data["l3_voltage_raw"] = basic_data[10]
                data["l1_current_raw"] = basic_data[11]
                data["l2_current_raw"] = basic_data[12]
                data["l3_current_raw"] = basic_data[13]
                data["power_raw"] = basic_data[14]
                data["lock_status"] = basic_data[15]
                data["phase_sequence"] = basic_data[16]
                data["max_power_raw"] = basic_data[17]
                data["min_power_raw"] = basic_data[18]
                data["max_current_raw"] = basic_data[19]
                data["min_current_raw"] = basic_data[20]
                data["alarm_code"] = basic_data[21]

            # Read energy registers (UINT32)
            current_energy_raw = self.modbus_client.read_uint32(0x1016)
            if current_energy_raw is not None:
                data["current_energy_raw"] = current_energy_raw

            total_energy_raw = self.modbus_client.read_uint32(0x1018)
            if total_energy_raw is not None:
                data["total_energy_raw"] = total_energy_raw

            fault_code = self.modbus_client.read_uint32(0x101A)
            if fault_code is not None:
                data["fault_code"] = fault_code

            rfid_card = self.modbus_client.read_uint32(0x101C)
            if rfid_card is not None:
                data["rfid_card"] = rfid_card

            # Read configuration registers (0x3000-0x300B)
            config_data = self.modbus_client.read_holding_registers(0x3000, 12)
            if config_data and len(config_data) >= 12:
                data["work_mode"] = config_data[0]
                data["max_charging_current_raw"] = config_data[1]
                data["max_charging_power_raw"] = config_data[2]
                data["allowed_charge_time"] = config_data[3]
                data["allowed_charge_energy"] = config_data[4]
                data["time_validity"] = config_data[5]
                data["default_current_raw"] = config_data[6]
                data["auto_phase_switch"] = config_data[10]
                data["min_switch_interval"] = config_data[11]

        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err

        return data
