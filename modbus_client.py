"""Modbus TCP client for FoxESS EV Charger."""
from __future__ import annotations

import logging
import socket

_LOGGER = logging.getLogger(__name__)

# ── Modbus Function Codes ─────────────────────────────────────────────────────
FC_READ_HOLDING     = 0x03   # Lesen R/W und R-Only Register
FC_WRITE_SINGLE     = 0x06   # Schreiben W-Only Register  (0x4000–0x4003)
FC_WRITE_MULTIPLE   = 0x10   # Schreiben R/W Register     (0x3000–0x300B)

# ── W-Only Register Adressen (FC 0x06) ───────────────────────────────────────
WRITE_ONLY_REGISTERS = {0x4000, 0x4001, 0x4002, 0x4003}


class FoxESSModbusClient:
    """Minimal Modbus TCP client (raw sockets, kein pymodbus)."""

    def __init__(self, host: str, port: int, slave_id: int) -> None:
        self._host      = host
        self._port      = port
        self._slave_id  = slave_id
        self._tid       = 0

    # ── Interne Hilfsmethoden ─────────────────────────────────────────────────

    def _next_tid(self) -> int:
        self._tid = (self._tid + 1) % 0xFFFF
        return self._tid

    def _send_recv(self, request: bytes, timeout: float = 5.0) -> bytes | None:
        try:
            with socket.create_connection((self._host, self._port), timeout=timeout) as sock:
                sock.sendall(request)
                return sock.recv(1024)
        except Exception as ex:
            _LOGGER.error("Modbus TCP %s:%s – Verbindungsfehler: %s", self._host, self._port, ex)
            return None

    def _build_mbap(self, pdu: bytes) -> bytes:
        """Baut den vollständigen Modbus TCP ADU (MBAP + PDU)."""
        tid     = self._next_tid()
        length  = 1 + len(pdu)   # Unit ID (1) + PDU
        return (
            tid.to_bytes(2, "big")              +  # Transaction ID
            (0).to_bytes(2, "big")              +  # Protocol ID
            length.to_bytes(2, "big")           +  # Length
            self._slave_id.to_bytes(1, "big")   +  # Unit ID
            pdu
        )

    # ── Öffentliche Methoden ──────────────────────────────────────────────────

    def read_registers(self, address: int, count: int) -> list[int] | None:
        """Liest `count` Holding-Register ab `address` (FC 0x03)."""
        pdu = (
            FC_READ_HOLDING.to_bytes(1, "big") +
            address.to_bytes(2, "big")         +
            count.to_bytes(2, "big")
        )
        response = self._send_recv(self._build_mbap(pdu))
        if response is None:
            return None

        # Modbus Exception prüfen
        if len(response) >= 9 and response[7] == (FC_READ_HOLDING | 0x80):
            _LOGGER.error("Modbus FC03 Exception 0x%02X @ 0x%04X", response[8], address)
            return None

        if len(response) < 9:
            _LOGGER.warning("FC03: zu kurze Antwort (%d Bytes)", len(response))
            return None

        byte_count = response[8]
        payload    = response[9: 9 + byte_count]
        registers  = [int.from_bytes(payload[i:i+2], "big") for i in range(0, byte_count, 2)]
        _LOGGER.debug("FC03 Read 0x%04X count=%d → %s", address, count, registers)
        return registers

    def read_uint32(self, address: int) -> int | None:
        """Liest einen UINT32-Wert aus zwei aufeinanderfolgenden Registern."""
        regs = self.read_registers(address, 2)
        if regs and len(regs) >= 2:
            return (regs[0] << 16) | regs[1]
        return None

    def write_holding_register(self, address: int, value: int) -> bool:
        """
        Schreibt ein einzelnes Register.

        R/W Register (0x3000–0x300B) → FC 0x10 (Write Multiple Registers)
        W-Only Register (0x4000–0x4003) → FC 0x06 (Write Single Register)
        """
        if address in WRITE_ONLY_REGISTERS:
            return self._write_single(address, value)
        else:
            return self._write_multiple(address, value)

    # ── Private Write-Methoden ────────────────────────────────────────────────

    def _write_single(self, address: int, value: int) -> bool:
        """FC 0x06 – Write Single Register (W-Only Register 0x4000–0x4003)."""
        pdu = (
            FC_WRITE_SINGLE.to_bytes(1, "big") +
            address.to_bytes(2, "big")         +
            value.to_bytes(2, "big")
        )
        response = self._send_recv(self._build_mbap(pdu))
        if response is None:
            return False

        if len(response) >= 9 and response[7] == (FC_WRITE_SINGLE | 0x80):
            _LOGGER.error(
                "FC06 Exception 0x%02X @ 0x%04X value=%d",
                response[8], address, value,
            )
            return False

        success = len(response) >= 12
        if success:
            _LOGGER.debug("FC06 Write 0x%04X = %d ✓", address, value)
        else:
            _LOGGER.warning(
                "FC06 Write 0x%04X = %d: unerwartete Antwort (%d Bytes): %s",
                address, value, len(response), response.hex(),
            )
        return success

    def _write_multiple(self, address: int, value: int) -> bool:
        """FC 0x10 – Write Multiple Registers (R/W Register 0x3000–0x300B)."""
        pdu = (
            FC_WRITE_MULTIPLE.to_bytes(1, "big") +
            address.to_bytes(2, "big")           +
            (1).to_bytes(2, "big")               +  # Quantity = 1 Register
            (2).to_bytes(1, "big")               +  # ByteCount = 2
            value.to_bytes(2, "big")
        )
        response = self._send_recv(self._build_mbap(pdu))
        if response is None:
            return False

        if len(response) >= 9 and response[7] == (FC_WRITE_MULTIPLE | 0x80):
            _LOGGER.error(
                "FC10 Exception 0x%02X @ 0x%04X value=%d",
                response[8], address, value,
            )
            return False

        success = len(response) >= 12
        if success:
            _LOGGER.debug("FC10 Write 0x%04X = %d ✓", address, value)
        else:
            _LOGGER.warning(
                "FC10 Write 0x%04X = %d: unerwartete Antwort (%d Bytes): %s",
                address, value, len(response), response.hex(),
            )
        return success

    def disconnect(self) -> None:
        """Kein persistenter Socket – nichts zu schließen."""
        pass
