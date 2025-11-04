"""Config flow for HA Narodmon Sender integration."""
from __future__ import annotations

import logging
import uuid
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback

from .const import DOMAIN, CONF_ALTITUDE, CONF_MAC_ADDRESS

_LOGGER = logging.getLogger(__name__)

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 360


def get_mac_address() -> str:
    """Return MAC address of current machine in format XX:XX:XX:XX:XX:XX."""
    mac = uuid.getnode()
    mac_str = ":".join(f"{(mac >> ele) & 0xff:02x}" for ele in range(40, -1, -8))
    return mac_str


class NarodmonSenderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Narodmon Sender."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="HA Narodmon Sender", data=user_input)

        # Defaults
        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude
        default_alt = getattr(self.hass.config, "elevation", 0.0)
        default_mac = get_mac_address()

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_LATITUDE, default=default_lat): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE, default=default_lon): vol.Coerce(float),
                vol.Optional(CONF_ALTITUDE, default=default_alt): vol.Coerce(float),
                vol.Optional(CONF_MAC_ADDRESS, default=default_mac): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=60, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow handler."""
        return NarodmonSenderOptionsFlow(config_entry)


class NarodmonSenderOptionsFlow(config_entries.OptionsFlow):
    """Handle options for HA Narodmon Sender."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        default_lat = self.config_entry.data.get(CONF_LATITUDE, self.hass.config.latitude)
        default_lon = self.config_entry.data.get(CONF_LONGITUDE, self.hass.config.longitude)
        default_alt = self.config_entry.data.get(CONF_ALTITUDE, getattr(self.hass.config, "elevation", 0.0))
        default_mac = self.config_entry.data.get(CONF_MAC_ADDRESS, get_mac_address())
        default_interval = self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_LATITUDE, default=default_lat): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE, default=default_lon): vol.Coerce(float),
                vol.Optional(CONF_ALTITUDE, default=default_alt): vol.Coerce(float),
                vol.Optional(CONF_MAC_ADDRESS, default=default_mac): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=default_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=60, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
