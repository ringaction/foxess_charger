"""Config flow for Fox ESS Charger integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    slave_id = data[CONF_SLAVE_ID]

    def test_connection():
        """Test connection to Modbus device."""
        try:
            from pymodbus.client import ModbusTcpClient
            
            client = ModbusTcpClient(host, port=port, timeout=5)
            if not client.connect():
                return False
            
            # Try to read device address
            result = client.read_holding_registers(0x1000, 1, slave=slave_id)
            client.close()
            
            return not result.isError()
        except Exception as err:
            _LOGGER.error("Connection test failed: %s", err)
            return False

    if not await hass.async_add_executor_job(test_connection):
        raise CannotConnect

    return {"title": f"Fox ESS Charger ({host})"}


class FoxESSChargerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fox ESS Charger."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(user_input[CONF_HOST])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
                
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.178.37"): cv.string,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=255)
                ),
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return FoxESSChargerOptionsFlow(config_entry)


class FoxESSChargerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=300)),
                }
            ),
        )
