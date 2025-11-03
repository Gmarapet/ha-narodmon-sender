import uuid
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from .const import (
    DOMAIN, CONF_MAC, CONF_INTERVAL, CONF_GROUPS, CONF_LATITUDE, CONF_LONGITUDE, CONF_ELEVATION,
    DEFAULT_INTERVAL, SUPPORTED_GROUPS, AGGREGATION_MODES
)

GROUP_KEYS = list(SUPPORTED_GROUPS.keys())

class NarodmonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return await self.async_step_groups(user_input)

        ha_lat = round(self.hass.config.latitude or 0.0, 6)
        ha_lon = round(self.hass.config.longitude or 0.0, 6)
        ha_alt = round(getattr(self.hass.config, "elevation", 0.0) or 0.0, 2)
        default_mac = uuid.uuid4().hex[:12].upper()

        schema = vol.Schema({
            vol.Required(CONF_MAC, default=default_mac): str,
            vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): int,
            vol.Optional(CONF_LATITUDE, default=ha_lat): float,
            vol.Optional(CONF_LONGITUDE, default=ha_lon): float,
            vol.Optional(CONF_ELEVATION, default=ha_alt): float,
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_groups(self, base_config):
        self._base_config = base_config
        self._base_config.setdefault(CONF_GROUPS, [])
        self._base_config.setdefault(CONF_CUSTOM, [])
        return await self.async_step_group_item()

    async def async_step_group_item(self, user_input=None):
        if user_input is not None:
            groups = self._base_config.get(CONF_GROUPS, [])
            groups.append(user_input)
            self._base_config[CONF_GROUPS] = groups
            if "add_another" in user_input and user_input.get("add_another"):
                return await self.async_step_group_item()
            return self.async_create_entry(title="HA Narodmon Sender", data=self._base_config)

        schema = vol.Schema({
            vol.Required("group_key", default=GROUP_KEYS[0]): vol.In(GROUP_KEYS),
            vol.Required("sensors"): selector({"entity": {"domain": "sensor", "multiple": True}}),
            vol.Required("aggregation", default="average"): selector({"select": {"options": AGGREGATION_MODES}}),
            vol.Optional("add_another", default=False): bool,
        })
        return self.async_show_form(step_id="group_item", data_schema=schema)

    async def async_step_custom(self, user_input=None):
        if user_input is not None:
            customs = self._base_config.get(CONF_CUSTOM, [])
            customs.append(user_input)
            self._base_config[CONF_CUSTOM] = customs
            if user_input.get("add_another"):
                return await self.async_step_custom()
            return self.async_create_entry(title="HA Narodmon Sender", data=self._base_config)

        schema = vol.Schema({
            vol.Required("identifier"): str,
            vol.Required("sensors"): selector({"entity": {"domain": "sensor", "multiple": True}}),
            vol.Optional("add_another", default=False): bool,
        })
        return self.async_show_form(step_id="custom", data_schema=schema)

    @staticmethod
    def async_get_options_flow(config_entry):
        return NarodmonOptionsFlowHandler(config_entry)


class NarodmonOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_abort(reason="not_implemented")
