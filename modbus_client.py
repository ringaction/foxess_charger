"""Modbus client for Fox ESS Charger using HA's modbus component."""
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform

_LOGGER = logging.getLogger(__name__)


class FoxESSModbusClient:
    """Fox ESS Modbus TCP client using Home Assistant's modbus."""

    def __init__(self, host: str, port: int, slave_id: int) -> None:
        """Initialize the Modbus client."""
        self._host = host
        self._port = port
        self._slave_id = slave_id
        self._pymodbus_client = None

    def _lazy_import_pymodbus(self):
        """Lazy import pymodbus to avoid loading issues."""
        if self._pymodbus_client is not None:
            return self._pymodbus_client
            
        try:
            from pymodbus.client import ModbusTcpClient
            self._pymodbus_client = ModbusTcpClient(
                self._host,
                port=self._port,
                timeout=5,
            )
            return self._pymodbus_client
        except Exception as ex:
            _LOGGER.error("Failed to import/create ModbusTcpClient: %s", ex)
            return None

    def connect(self) -> bool:
        """Connect to the Modbus device."""
        client = self._lazy_import_pymodbus()
        if not client:
            return False
            
        try:
            result = client.connect()
            if result:
                _LOGGER.info("Connected to %s:%s", self._host, self._port)
            return result
        except Exception as ex:
            _LOGGER.error("Connection error: %s", ex)
            return False

    def disconnect(self) -> None:
        """Disconnect from the Modbus device."""
        if self._pymodbus_client:
            try:
                self._pymodbus_client.close()
            except:
                pass
            self._pymodbus_client = None

    def read_holding_registers(self, address: int, count: int) -> list[int] | None:
        """Read holding registers using low-level pymodbus."""
        client = self._lazy_import_pymodbus()
        if not client:
            return None
            
        if not self.connect():
            return None
        
        try:
            # Build the raw PDU request
            # Function code 0x03 = Read Holding Registers
            pdu = bytes([0x03]) + address.to_bytes(2, 'big') + count.to_bytes(2, 'big')
            
            # Send raw request
            from pymodbus.transaction import ModbusSocketFramer
            from pymodbus.framer import ModbusFramer
            
            # Use the client's framer to build and send request
            request_pdu = client.framer.buildPacket(pdu)
            client.socket.send(request_pdu)
            
            # Receive response
            response_pdu = client.socket.recv(1024)
            response = client.framer.processIncomingPacket(response_pdu)
            
            # Parse response
            if response and len(response) > 2:
                byte_count = response[2]
                registers = []
                for i in range(0, byte_count, 2):
                    reg_value = int.from_bytes(response[3+i:5+i], 'big')
                    registers.append(reg_value)
                return registers
                
            return None
            
        except Exception as ex:
            _LOGGER.debug("Low-level read failed (expected, using raw socket): %s", ex)

            
            # Ultimate fallback: raw socket
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self._host, self._port))
                
                # MODBUS TCP/IP ADU = Transaction ID + Protocol ID + Length + Unit ID + PDU
                transaction_id = 1
                protocol_id = 0
                length = 6  # Unit ID (1) + Function Code (1) + Address (2) + Count (2)
                unit_id = self._slave_id
                function_code = 0x03
                
                # Build request
                request = (
                    transaction_id.to_bytes(2, 'big') +
                    protocol_id.to_bytes(2, 'big') +
                    length.to_bytes(2, 'big') +
                    unit_id.to_bytes(1, 'big') +
                    function_code.to_bytes(1, 'big') +
                    address.to_bytes(2, 'big') +
                    count.to_bytes(2, 'big')
                )
                
                sock.send(request)
                response = sock.recv(1024)
                sock.close()
                
                # Parse MODBUS TCP response
                # Skip: Trans ID (2) + Proto ID (2) + Length (2) + Unit ID (1) + Func (1)
                if len(response) > 9:
                    byte_count = response[8]
                    registers = []
                    for i in range(0, byte_count, 2):
                        reg_value = int.from_bytes(response[9+i:11+i], 'big')
                        registers.append(reg_value)
                    _LOGGER.info("Raw socket read successful!")
                    return registers
                    
            except Exception as sock_ex:
                _LOGGER.error("Raw socket read failed: %s", sock_ex)
                
            return None

    def write_register(self, address: int, value: int) -> bool:
        """Write single register."""
        if not self.connect():
            return False
            
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self._host, self._port))
            
            # MODBUS TCP Write Single Register (0x06)
            transaction_id = 1
            protocol_id = 0
            length = 6
            unit_id = self._slave_id
            function_code = 0x06
            
            request = (
                transaction_id.to_bytes(2, 'big') +
                protocol_id.to_bytes(2, 'big') +
                length.to_bytes(2, 'big') +
                unit_id.to_bytes(1, 'big') +
                function_code.to_bytes(1, 'big') +
                address.to_bytes(2, 'big') +
                value.to_bytes(2, 'big')
            )
            
            sock.send(request)
            response = sock.recv(1024)
            sock.close()
            
            # Check if response echoes the request (successful write)
            return len(response) >= 12
            
        except Exception as ex:
            _LOGGER.error("Write failed: %s", ex)
            return False

    def read_uint32(self, address: int) -> int | None:
        """Read 32-bit unsigned integer (2 registers)."""
        registers = self.read_holding_registers(address, 2)
        if registers and len(registers) >= 2:
            return (registers[0] << 16) | registers[1]
        return None
