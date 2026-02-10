"""Sensor platform for Fox ESS Charger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    STATUS_MAP,
    CP_STATUS_MAP,
    WORK_MODE_MAP,
    PHASE_SEQUENCE_MAP,
    STOP_REASON_MAP,
)


@dataclass
class FoxESSChargerSensorDescription(SensorEntityDescription):
    """Describes Fox ESS Charger sensor entity."""

    value_fn: Callable[[dict], StateType] | None = None


SENSORS: tuple[FoxESSChargerSensorDescription, ...] = (
    # System Information
    FoxESSChargerSensorDescription(
        key="software_version",
        name="Software Version",
        icon="mdi:information-outline",
        value_fn=lambda data: f"{(data.get('software_version', 0) >> 8)}.{(data.get('software_version', 0) & 0xFF)}",
    ),
    FoxESSChargerSensorDescription(
        key="device_address",
        name="Device Address",
        icon="mdi:identifier",
        value_fn=lambda data: data.get("device_address"),
    ),
    # Status
    FoxESSChargerSensorDescription(
        key="status",
        name="Status",
        icon="mdi:ev-station",
        device_class=SensorDeviceClass.ENUM,
        options=list(STATUS_MAP.values()),
        value_fn=lambda data: STATUS_MAP.get(data.get("status", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="cp_status",
        name="CP Status",
        icon="mdi:connection",
        device_class=SensorDeviceClass.ENUM,
        options=list(CP_STATUS_MAP.values()),
        value_fn=lambda data: CP_STATUS_MAP.get(data.get("cp_status", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="cc_status",
        name="CC Status",
        icon="mdi:cable-data",
        device_class=SensorDeviceClass.ENUM,
        options=["disconnected", "connected"],
        value_fn=lambda data: "connected" if data.get("cc_status") == 1 else "disconnected",
    ),
    FoxESSChargerSensorDescription(
        key="lock_status",
        name="Lock Status",
        icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM,
        options=["unlocked", "locked"],
        value_fn=lambda data: "locked" if data.get("lock_status") == 1 else "unlocked",
    ),
    FoxESSChargerSensorDescription(
        key="work_mode",
        name="Work Mode",
        icon="mdi:cog",
        device_class=SensorDeviceClass.ENUM,
        options=list(WORK_MODE_MAP.values()),
        value_fn=lambda data: WORK_MODE_MAP.get(data.get("work_mode", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="phase_sequence",
        name="Phase Sequence",
        icon="mdi:electric-switch",
        device_class=SensorDeviceClass.ENUM,
        options=list(PHASE_SEQUENCE_MAP.values()),
        value_fn=lambda data: PHASE_SEQUENCE_MAP.get(data.get("phase_sequence", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="stop_reason",
        name="Stop Reason",
        icon="mdi:information",
        value_fn=lambda data: STOP_REASON_MAP.get(data.get("stop_reason", 0), "unknown"),
    ),
    # Temperatures
    FoxESSChargerSensorDescription(
        key="port_temperature",
        name="Charging Port Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
        value_fn=lambda data: round(data.get("port_temp_raw", 0) * 0.1 - 50, 1)
        if data.get("port_temp_raw", 65535) != 65535
        else None,
    ),
    FoxESSChargerSensorDescription(
        key="ambient_temperature",
        name="Ambient Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
        value_fn=lambda data: round(data.get("ambient_temp_raw", 0) * 0.1 - 50, 1),
    ),
    # Voltages
    FoxESSChargerSensorDescription(
        key="l1_voltage",
        name="L1 Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:flash",
        value_fn=lambda data: round(data.get("l1_voltage_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l2_voltage",
        name="L2 Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:flash",
        value_fn=lambda data: round(data.get("l2_voltage_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l3_voltage",
        name="L3 Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:flash",
        value_fn=lambda data: round(data.get("l3_voltage_raw", 0) * 0.1, 1),
    ),
    # Currents
    FoxESSChargerSensorDescription(
        key="l1_current",
        name="L1 Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda data: round(data.get("l1_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l2_current",
        name="L2 Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda data: round(data.get("l2_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l3_current",
        name="L3 Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda data: round(data.get("l3_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="total_current",
        name="Total Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda data: round(
            (data.get("l1_current_raw", 0) + data.get("l2_current_raw", 0) + data.get("l3_current_raw", 0)) * 0.1,
            1,
        ),
    ),
    # Power
    FoxESSChargerSensorDescription(
        key="charging_power",
        name="Charging Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        icon="mdi:lightning-bolt",
        value_fn=lambda data: round(data.get("power_raw", 0) * 0.1, 2),
    ),
    FoxESSChargerSensorDescription(
        key="max_power",
        name="Max Supported Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        icon="mdi:lightning-bolt",
        value_fn=lambda data: round(data.get("max_power_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="min_power",
        name="Min Supported Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        icon="mdi:lightning-bolt",
        value_fn=lambda data: round(data.get("min_power_raw", 0) * 0.1, 1),
    ),
    # Current Limits
    FoxESSChargerSensorDescription(
        key="max_current",
        name="Max Supported Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda data: round(data.get("max_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="min_current",
        name="Min Supported Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda data: round(data.get("min_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="default_current",
        name="Default Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda data: round(data.get("default_current_raw", 0) * 0.1, 1),
    ),
    # Energy
    FoxESSChargerSensorDescription(
        key="current_energy",
        name="Current Session Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:counter",
        value_fn=lambda data: round(data.get("current_energy_raw", 0) * 0.1, 2),
    ),
    FoxESSChargerSensorDescription(
        key="total_energy",
        name="Total Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:counter",
        value_fn=lambda data: round(data.get("total_energy_raw", 0) * 0.1, 2),
    ),
    # Time Settings
    FoxESSChargerSensorDescription(
        key="allowed_charge_time",
        name="Allowed Charge Time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer",
        value_fn=lambda data: data.get("allowed_charge_time"),
    ),
    FoxESSChargerSensorDescription(
        key="allowed_charge_energy",
        name="Allowed Charge Energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:battery-charging",
        value_fn=lambda data: data.get("allowed_charge_energy"),
    ),
    FoxESSChargerSensorDescription(
        key="time_validity",
        name="Time Validity",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:clock-outline",
        value_fn=lambda data: data.get("time_validity"),
    ),
    FoxESSChargerSensorDescription(
        key="min_switch_interval",
        name="Min Switch Interval",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-sand",
        value_fn=lambda data: data.get("min_switch_interval"),
    ),
    # Codes
    FoxESSChargerSensorDescription(
        key="alarm_code",
        name="Alarm Code",
        icon="mdi:alert",
        value_fn=lambda data: data.get("alarm_code"),
    ),
    FoxESSChargerSensorDescription(
        key="fault_code",
        name="Fault Code",
        icon="mdi:alert-circle",
        value_fn=lambda data: data.get("fault_code"),
    ),
    FoxESSChargerSensorDescription(
        key="rfid_card",
        name="RFID Card",
        icon="mdi:card-account-details",
        value_fn=lambda data: f"{data.get('rfid_card', 0):08X}" if data.get("rfid_card", 0) > 0 else "None",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fox ESS Charger sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        FoxESSChargerSensor(coordinator, description, entry)
        for description in SENSORS
    ]

    async_add_entities(entities)


class FoxESSChargerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Fox ESS Charger sensor."""

    entity_description: FoxESSChargerSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: FoxESSChargerSensorDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Fox ESS Charger",
            "manufacturer": "Fox ESS",
            "model": "EV Charger",
            "sw_version": self._get_software_version(),
        }

    def _get_software_version(self) -> str:
        """Get software version from coordinator data."""
        if self.coordinator.data:
            sw_ver = self.coordinator.data.get("software_version", 0)
            return f"{sw_ver >> 8}.{sw_ver & 0xFF}"
        return "Unknown"

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
