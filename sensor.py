"""Sensors for FoxESS EV Charger."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent, UnitOfElectricPotential,
    UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATUS_MAP, CP_STATUS_MAP, WORK_MODE_MAP, PHASE_SEQ_MAP, STOP_REASON_MAP
from .__init__ import FoxESSChargerCoordinator


@dataclass(frozen=True, kw_only=True)
class FoxESSChargerSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], StateType] = lambda _: None


SENSORS: tuple[FoxESSChargerSensorDescription, ...] = (
    # ── System ──────────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="software_version", name="Software Version", icon="mdi:information-outline",
        value_fn=lambda d: f"{d.get('software_version',0)>>8}.{d.get('software_version',0)&0xFF}",
    ),
    FoxESSChargerSensorDescription(
        key="device_address", name="Device Address", icon="mdi:identifier",
        value_fn=lambda d: d.get("device_address"),
    ),
    # ── Status ───────────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="status", name="Status", icon="mdi:ev-station",
        device_class=SensorDeviceClass.ENUM,
        options=list(STATUS_MAP.values()),
        value_fn=lambda d: STATUS_MAP.get(d.get("status", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="cp_status", name="CP Status", icon="mdi:connection",
        device_class=SensorDeviceClass.ENUM, options=list(CP_STATUS_MAP.values()),
        value_fn=lambda d: CP_STATUS_MAP.get(d.get("cp_status", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="cc_status", name="CC Status", icon="mdi:cable-data",
        device_class=SensorDeviceClass.ENUM, options=["disconnected", "connected"],
        value_fn=lambda d: "connected" if d.get("cc_status") == 1 else "disconnected",
    ),
    FoxESSChargerSensorDescription(
        key="lock_status", name="Lock Status", icon="mdi:lock",
        device_class=SensorDeviceClass.ENUM, options=["unlocked", "locked"],
        value_fn=lambda d: "locked" if d.get("lock_status") == 1 else "unlocked",
    ),
    FoxESSChargerSensorDescription(
        key="work_mode_sensor", name="Work Mode", icon="mdi:cog",
        device_class=SensorDeviceClass.ENUM, options=list(WORK_MODE_MAP.values()),
        value_fn=lambda d: WORK_MODE_MAP.get(d.get("work_mode", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="phase_sequence", name="Phase Sequence", icon="mdi:electric-switch",
        device_class=SensorDeviceClass.ENUM, options=list(PHASE_SEQ_MAP.values()),
        value_fn=lambda d: PHASE_SEQ_MAP.get(d.get("phase_sequence", 0), "unknown"),
    ),
    FoxESSChargerSensorDescription(
        key="stop_reason", name="Stop Reason", icon="mdi:information",
        value_fn=lambda d: STOP_REASON_MAP.get(d.get("stop_reason", 0), "unknown"),
    ),
    # ── Temperaturen ─────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="port_temperature", name="Port Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
        value_fn=lambda d: round(d["port_temp_raw"] * 0.1 - 50, 1)
            if d.get("port_temp_raw") not in (None, 65535) else None,
    ),
    FoxESSChargerSensorDescription(
        key="ambient_temperature", name="Ambient Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        icon="mdi:thermometer",
        value_fn=lambda d: round(d.get("ambient_temp_raw", 0) * 0.1 - 50, 1),
    ),
    # ── Spannungen ───────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="l1_voltage", name="L1 Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:flash",
        value_fn=lambda d: round(d.get("l1_voltage_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l2_voltage", name="L2 Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:flash",
        value_fn=lambda d: round(d.get("l2_voltage_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l3_voltage", name="L3 Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        icon="mdi:flash",
        value_fn=lambda d: round(d.get("l3_voltage_raw", 0) * 0.1, 1),
    ),
    # ── Ströme ───────────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="l1_current", name="L1 Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda d: round(d.get("l1_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l2_current", name="L2 Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda d: round(d.get("l2_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="l3_current", name="L3 Current",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda d: round(d.get("l3_current_raw", 0) * 0.1, 1),
    ),
    # ── Leistung ─────────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="charging_power", name="Charging Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        icon="mdi:lightning-bolt",
        value_fn=lambda d: round(d.get("power_raw", 0) * 0.1, 2),
    ),
    FoxESSChargerSensorDescription(
        key="max_supported_power", name="Max Supported Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        icon="mdi:lightning-bolt-outline",
        value_fn=lambda d: round(d.get("max_power_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="min_supported_power", name="Min Supported Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        icon="mdi:lightning-bolt-outline",
        value_fn=lambda d: round(d.get("min_power_raw", 0) * 0.1, 1),
    ),
    # ── Strom-Limits ─────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="max_supported_current", name="Max Supported Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda d: round(d.get("max_current_raw", 0) * 0.1, 1),
    ),
    FoxESSChargerSensorDescription(
        key="min_supported_current", name="Min Supported Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        icon="mdi:current-ac",
        value_fn=lambda d: round(d.get("min_current_raw", 0) * 0.1, 1),
    ),
    # ── Energie ──────────────────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="current_session_energy", name="Current Session Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:counter",
        value_fn=lambda d: round(d.get("current_energy_raw", 0) * 0.1, 2),
    ),
    FoxESSChargerSensorDescription(
        key="total_energy", name="Total Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        icon="mdi:counter",
        value_fn=lambda d: round(d.get("total_energy_raw", 0) * 0.1, 2),
    ),
    # ── Konfigurationssensoren ────────────────────────────────────────────────
    FoxESSChargerSensorDescription(
        key="alarm_code", name="Alarm Code", icon="mdi:alert",
        value_fn=lambda d: d.get("alarm_code"),
    ),
    FoxESSChargerSensorDescription(
        key="fault_code", name="Fault Code", icon="mdi:alert-circle",
        value_fn=lambda d: d.get("fault_code"),
    ),
    FoxESSChargerSensorDescription(
        key="rfid_card", name="RFID Card", icon="mdi:card-account-details",
        value_fn=lambda d: f"{d.get('rfid_card',0):08X}" if d.get("rfid_card", 0) > 0 else "None",
    ),
)

DEVICE_INFO_TEMPLATE = DeviceInfo(
    manufacturer="FoxESS", model="A011 EV Charger",
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FoxESSChargerCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        FoxESSChargerSensor(coordinator, desc, entry) for desc in SENSORS
    ])


class FoxESSChargerSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True
    entity_description: FoxESSChargerSensorDescription

    def __init__(self, coordinator: FoxESSChargerCoordinator,
                 description: FoxESSChargerSensorDescription, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="FoxESS Charger", manufacturer="FoxESS", model="A011",
        )

    @property
    def native_value(self) -> StateType:
        if self.coordinator.data and self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None
