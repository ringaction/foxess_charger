"""Constants for Fox ESS Charger integration."""
from homeassistant.const import Platform

DOMAIN = "foxess_charger"
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SWITCH,
]

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SLAVE_ID = "slave_id"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_PORT = 1502
DEFAULT_SLAVE_ID = 1
DEFAULT_SCAN_INTERVAL = 5

# Modbus Register Addresses
REG_DEVICE_ADDRESS = 0x1000
REG_SOFTWARE_VERSION = 0x1001
REG_STOP_REASON = 0x1002
REG_STATUS = 0x1003
REG_CP_STATUS = 0x1004
REG_CC_STATUS = 0x1005
REG_PORT_TEMP = 0x1006
REG_AMBIENT_TEMP = 0x1007
REG_L1_VOLTAGE = 0x1008
REG_L2_VOLTAGE = 0x1009
REG_L3_VOLTAGE = 0x100A
REG_L1_CURRENT = 0x100B
REG_L2_CURRENT = 0x100C
REG_L3_CURRENT = 0x100D
REG_ACTIVE_POWER = 0x100E
REG_LOCK_STATUS = 0x100F
REG_PHASE_SEQUENCE = 0x1010
REG_MAX_POWER = 0x1011
REG_MIN_POWER = 0x1012
REG_MAX_CURRENT = 0x1013
REG_MIN_CURRENT = 0x1014
REG_ALARM_CODE = 0x1015
REG_CURRENT_ENERGY = 0x1016
REG_TOTAL_ENERGY = 0x1018
REG_FAULT_CODE = 0x101A
REG_RFID_CARD = 0x101C

# Read/Write Registers
REG_WORK_MODE = 0x3000
REG_MAX_CHARGING_CURRENT = 0x3001
REG_MAX_CHARGING_POWER = 0x3002
REG_ALLOWED_CHARGE_TIME = 0x3003
REG_ALLOWED_CHARGE_ENERGY = 0x3004
REG_TIME_VALIDITY = 0x3005
REG_DEFAULT_CURRENT = 0x3006
REG_AUTO_PHASE_SWITCH = 0x300A
REG_MIN_SWITCH_INTERVAL = 0x300B

# Write-Only Registers
REG_LOCK_CONTROL = 0x4000
REG_CHARGING_CONTROL = 0x4001
REG_PHASE_SWITCHING = 0x4002
REG_RESTART = 0x4003

# Status mappings
STATUS_MAP = {
    0: "idle",
    1: "connected",
    2: "ready",
    3: "charging",
    4: "paused",
    5: "finished",
    6: "fault",
    7: "reserved",
    8: "locked",
}

CP_STATUS_MAP = {
    0: "fault",
    1: "12v_disconnected",
    2: "9v_connected",
    3: "6v_ready",
}

WORK_MODE_MAP = {
    0: "controlled",
    1: "plug_and_charge",
    2: "locked",
}

PHASE_SEQUENCE_MAP = {
    0: "three_phase",
    1: "l2_single_phase",
    2: "l3_single_phase",
    3: "reserved",
}

STOP_REASON_MAP = {
    0: "none",
    1: "command",
    2: "time_completed",
    3: "s2_timeout",
    4: "pause_timeout",
    5: "emergency_stop",
    6: "cp_voltage_abnormal",
    7: "connector_pulled",
    8: "ac_contactor_abnormal",
    9: "lock_abnormal",
    10: "card_reader_abnormal",
    11: "overcurrent",
    12: "overvoltage",
    13: "undervoltage",
    14: "port_overtemp",
    15: "leakage_current",
    16: "n_line_reversed",
    17: "frequency_abnormal",
    18: "stop_button_pressed",
    19: "breaker_abnormal",
    20: "phase_loss",
    21: "pe_abnormal",
    22: "external_meter_abnormal",
    23: "ambient_overtemp",
    24: "metering_chip_fault",
    25: "access_control_fault",
    26: "pbox_phase_switch_abnormal",
    27: "energy_limit_reached",
}
