from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    LOGGER,
)

# Standardwerte – ggf. anpassen
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 10  # Sekunden


def _build_user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                "host",
                default=defaults.get("host", ""),
            ): str,
            vol.Required(
                "port",
                default=defaults.get("port", DEFAULT_PORT),
            ): int,
            vol.Required(
                "unit_id",
                default=defaults.get("unit_id", DEFAULT_UNIT_ID),
            ): int,
        }
    )


def _build_options_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                "scan_interval",
                default=defaults.get("scan_interval", DEFAULT_SCAN_INTERVAL),
            ): int,
        }
    )


class FoxESSChargerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FoxESS Charger."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input["host"]
            port = user_input["port"]
            unit_id = user_input["unit_id"]

            # Eindeutige ID pro Charger (Host+Unit ID)
            unique_id = f"{host}-{unit_id}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            LOGGER.debug(
                "FoxESS Charger: creating config entry host=%s port=%s unit_id=%s",
                host,
                port,
                unit_id,
            )

            return self.async_create_entry(
                title=f"FoxESS Charger ({host})",
                data={
                    "host": host,
                    "port": port,
                    "unit_id": unit_id,
                },
                options={
                    "scan_interval": DEFAULT_SCAN_INTERVAL,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_build_user_schema(),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return FoxESSChargerOptionsFlow(config_entry)


class FoxESSChargerOptionsFlow(OptionsFlow):
    """Handle FoxESS Charger options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize FoxESS Charger options flow."""
        # intern speichern, keine Property überschreiben
        self._config_entry = config_entry

    @property
    def config_entry(self) -> ConfigEntry:
        """Return the config entry."""
        return self._config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options."""
        errors: dict[str, str] = {}

        current_options = {
            "scan_interval": self._config_entry.options.get(
                "scan_interval",
                DEFAULT_SCAN_INTERVAL,
            ),
        }

        if user_input is not None:
            scan_interval = user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL)
            if scan_interval < 5:
                errors["base"] = "scan_interval_too_low"
            else:
                LOGGER.debug(
                    "FoxESS Charger: updating options scan_interval=%s",
                    scan_interval,
                )
                return self.async_create_entry(
                    title="",
                    data={"scan_interval": scan_interval},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_build_options_schema(current_options),
            errors=errors,
        )
