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

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fox ESS Charger from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    slave_id = entry.data[CONF_SLAVE_ID]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    coordinator = FoxESSChargerCoordinator(
        hass, host, port, slave_id, scan_interval
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
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class FoxESSChargerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Fox ESS Charger data."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        slave_id: int,
        scan_interval: int,
    ) -> None:
        """Initialize."""
        self.host = host
        self.port = port
        self.slave_id = slave_id
        self.client = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _connect(self) -> bool:
        """Connect to Modbus device."""
        try:
            from pymodbus.client import ModbusTcpClient
            
            if self.client is None or not self.client.connected:
                self.client = ModbusTcpClient(self.host, port=self.port, timeout=5)
                self.client.connect()
            return self.client.connected
        except Exception as err:
            _LOGGER.error("Failed to connect to %s:%s - %s", self.host, self.port, err)
            return False

    def _read_registers(self, address: int, count: int = 1) -> list | None:
        """Read Modbus registers."""
        try:
            if not self._connect():
                return None

            result = self.client.read_holding_registers(
                address, count, slave=self.slave_id
            )

            if result.isError():
                _LOGGER.error("Modbus read error at address 0x%04X", address)
                return None

            return result.registers
        except Exception as err:
            _LOGGER.error("Error reading registers: %s", err)
            return None

    def write_register(self, address: int, value: int) -> bool:
        """Write to a Modbus register."""
        try:
            if not self._connect():
                return False

            result = self.client.write_register(address, value, slave=self.slave_id)

            if result.isError():
                _LOGGER.error("Modbus write error at address 0x%04X", address)
                return False

            return True
        except Exception as err:
            _LOGGER.error("Error writing register: %s", err)
            return False

    async def _async_update_data(self):
        """Fetch data from the device."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    def _fetch_data(self) -> dict:
        """Fetch all data from Modbus registers."""
        data = {}

        # Read basic status registers (0x1000-0x1015)
        basic_data = self._read_registers(0x1000, 22)
        if basic_data:
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
        current_energy = self._read_registers(0x1016, 2)
        if current_energy:
            data["current_energy_raw"] = (current_energy[0] << 16) | current_energy[1]

        total_energy = self._read_registers(0x1018, 2)
        if total_energy:
            data["total_energy_raw"] = (total_energy[0] << 16) | total_energy[1]

        fault_code = self._read_registers(0x101A, 2)
        if fault_code:
            data["fault_code"] = (fault_code[0] << 16) | fault_code[1]

        rfid = self._read_registers(0x101C, 2)
        if rfid:
            data["rfid_card"] = (rfid[0] << 16) | rfid[1]

        # Read configuration registers (0x3000-0x300B)
        config_data = self._read_registers(0x3000, 12)
        if config_data:
            data["work_mode"] = config_data[0]
            data["max_charging_current_raw"] = config_data[1]
            data["max_charging_power_raw"] = config_data[2]
            data["allowed_charge_time"] = config_data[3]
            data["allowed_charge_energy"] = config_data[4]
            data["time_validity"] = config_data[5]
            data["default_current_raw"] = config_data[6]
            # 0x3007-0x3009 skipped
            data["auto_phase_switch"] = config_data[10]  # 0x300A
            data["min_switch_interval"] = config_data[11]  # 0x300B

        return data
