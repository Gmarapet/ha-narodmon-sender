"""Config flow + Options flow for HA Narodmon Sender integration."""
from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import callback
from homeassistant.helpers.selector import selector

from .const import (
    DOMAIN,
    CONF_ALTITUDE,
    CONF_MAC_ADDRESS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    SUPPORTED_SENSOR_TYPES,
    AGGREGATION_MODES,
    SENSOR_TYPE_MATCH,
)

_LOGGER = logging.getLogger(__name__)


def get_mac_address() -> str:
    """Return MAC address of current machine in format XX:XX:XX:XX:XX:XX."""
    mac = uuid.getnode()
    mac_str = ":".join(f"{(mac >> ele) & 0xFF:02x}" for ele in range(40, -1, -8))
    return mac_str


class NarodmonSenderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Narodmon Sender."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial configuration (basic parameters)."""
        errors = {}

        if user_input is not None:
            # store base settings in config entry data
            return self.async_create_entry(title="HA Narodmon Sender", data=user_input)

        default_lat = self.hass.config.latitude
        default_lon = self.hass.config.longitude
        default_alt = getattr(self.hass.config, "elevation", 0.0)
        default_mac = get_mac_address()

        schema = vol.Schema(
            {
                vol.Optional(CONF_LATITUDE, default=default_lat): vol.Coerce(float),
                vol.Optional(CONF_LONGITUDE, default=default_lon): vol.Coerce(float),
                vol.Optional(CONF_ALTITUDE, default=default_alt): vol.Coerce(float),
                vol.Optional(CONF_MAC_ADDRESS, default=default_mac): str,
                vol.Optional(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow handler."""
        return NarodmonSenderOptionsFlow(config_entry)


class NarodmonSenderOptionsFlow(config_entries.OptionsFlow):
    """Options flow to manage groups and base settings."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        # working copy of options to edit during flow
        self._options = dict(config_entry.options or {})
        self._working_group_index: int | None = None

    def _get_groups(self) -> list[dict]:
        return self._options.get("groups", [])

    def _save_groups(self, groups: list[dict]) -> None:
        self._options["groups"] = groups

    def _match_sensor_type(self, sensor_state, wanted_type: str) -> bool:
        """Heuristic: check device_class first, then unit_of_measurement substr."""
        attrs = sensor_state.attributes
        device_class = attrs.get("device_class")
        unit = attrs.get("unit_of_measurement") or ""
        match = SENSOR_TYPE_MATCH.get(wanted_type)
        if not match:
            return False
        # device_class match
        if device_class and match["device_class"]:
            if isinstance(match["device_class"], (list, tuple)):
                if device_class in match["device_class"]:
                    return True
            elif device_class == match["device_class"]:
                return True
        # unit substring check
        for sub in match.get("unit_substr", []):
            if sub and sub in str(unit):
                return True
        return False

    def _enum_sensors_for_type(self, type_key: str, restrict_by_first: str | None = None) -> list[dict]:
        """Return list of sensors (as dicts suitable for selector options) matching given type.
        If restrict_by_first is provided (entity_id), further restrict to sensors that match same device_class/unit as that first sensor.
        """
        options = []
        first_device_class = None
        first_unit = None

        if restrict_by_first:
            first_state = self.hass.states.get(restrict_by_first)
            if first_state:
                first_device_class = first_state.attributes.get("device_class")
                first_unit = first_state.attributes.get("unit_of_measurement")

        for st in self.hass.states.async_all(domain="sensor"):
            # Skip sensors without state maybe
            # if not st.state or st.state in ("unknown", "unavailable"):
            #     continue
            # If restrict_by_first is set, enforce device_class/unit equality
            if restrict_by_first and first_device_class is not None:
                if st.attributes.get("device_class") != first_device_class:
                    continue
                # if first_unit and st.attributes.get("unit_of_measurement") != first_unit:
                #     continue
            # If type_key == "custom" allow all
            if type_key == "custom":
                options.append({"label": f"{st.entity_id} — {st.name}", "value": st.entity_id})
                continue

            if self._match_sensor_type(st, type_key):
                options.append({"label": f"{st.entity_id} — {st.name}", "value": st.entity_id})

        # Sort options by label
        options.sort(key=lambda x: x["label"])
        return options

    async def async_step_init(self, user_input: dict | None = None):
        """Top-level options: manage base settings and navigate to group management."""
        if user_input is not None:
            # user pressed action; but we will use explicit action handling below
            pass

        groups = self._get_groups()
        # Prepare action options: Add group + per-group Edit/Delete
        action_options = [{"label": "Добавить новую группу", "value": "add"}]
        for idx, g in enumerate(groups):
            action_options.append({"label": f"Редактировать: {g.get('name','group_'+str(idx))}", "value": f"edit:{idx}"})
            action_options.append({"label": f"Удалить: {g.get('name','group_'+str(idx))}", "value": f"delete:{idx}"})

        schema = vol.Schema(
            {
                vol.Optional("update_interval", default=self.config_entry.options.get(CONF_UPDATE_INTERVAL, self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL))): vol.All(
                    vol.Coerce(int), vol.Range(min=30, max=86400)
                ),
                vol.Optional("action", default="noop"): selector({"select": {"options": action_options}}),
            }
        )

        if user_input is None:
            return self.async_show_form(step_id="init", data_schema=schema)

        # Handle submitted form
        action = user_input.get("action")
        # save update_interval to options
        self._options[CONF_UPDATE_INTERVAL] = user_input.get("update_interval", self.config_entry.options.get(CONF_UPDATE_INTERVAL, self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)))

        if not action or action == "noop":
            # finish and save options
            return self.async_create_entry(title="", data=self._options)

        if action == "add":
            # start add flow
            return await self.async_step_add_group()

        if action.startswith("edit:"):
            idx = int(action.split(":", 1)[1])
            return await self.async_step_edit_group({"index": idx})

        if action.startswith("delete:"):
            idx = int(action.split(":", 1)[1])
            groups.pop(idx)
            self._save_groups(groups)
            # return to init to show updated list
            return await self.async_step_init()

        # fallback
        return self.async_create_entry(title="", data=self._options)

    async def async_step_add_group(self, user_input: dict | None = None):
        """Step to create a new group: name, type, aggregation."""
        if user_input is not None:
            # initialize group skeleton and go to sensors selection
            new_group = {
                "name": user_input["name"],
                "type": user_input["type"],
                "aggregation": user_input["aggregation"],
                "sensors": user_input.get("sensors", []),
            }
            groups = self._get_groups()
            groups.append(new_group)
            self._save_groups(groups)
            # If sensors not chosen yet, go to edit the last group to pick sensors
            if not new_group["sensors"]:
                return await self.async_step_edit_group({"index": len(groups) - 1})
            return await self.async_step_init()

        # Prepare type options (include custom)
        type_options = []
        for k in list(SUPPORTED_SENSOR_TYPES.keys()) + ["custom"]:
            type_options.append({"label": f"{k}", "value": k})

        schema = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Required("type", default="temperature"): selector({"select": {"options": type_options}}),
                vol.Required("aggregation", default=AGGREGATION_MODES[2]): selector({"select": {"options": [{"label": a, "value": a} for a in AGGREGATION_MODES]}}),
                # optional quick pick sensors (we will also allow editing sensors later)
                vol.Optional("sensors", default=[]): selector({"select": {"options": [], "multiple": True}}),
            }
        )

        return self.async_show_form(step_id="add_group", data_schema=schema)

    async def async_step_edit_group(self, user_input: dict | None = None):
        """Edit sensors of specific group (index passed in start)."""
        # If called directly with index
        idx = None
        if user_input and "index" in user_input:
            idx = int(user_input["index"])
            # show edit form
            groups = self._get_groups()
            if idx < 0 or idx >= len(groups):
                return await self.async_step_init()
            self._working_group_index = idx
            group = groups[idx]
            # compute options for sensor selector based on group type and possibly first sensor
            restrict_first = None
            if group.get("sensors"):
                restrict_first = group["sensors"][0]
            options = self._enum_sensors_for_type(group.get("type", "custom"), restrict_by_first=restrict_first)
            schema = vol.Schema(
                {
                    vol.Required("name", default=group.get("name", "")): str,
                    vol.Optional("aggregation", default=group.get("aggregation", AGGREGATION_MODES[2])): selector({"select": {"options": [{"label": a, "value": a} for a in AGGREGATION_MODES]}}),
                    vol.Optional("sensors", default=group.get("sensors", [])): selector({"select": {"options": options, "multiple": True}}),
                    vol.Optional("done", default=False): bool,
                }
            )
            return self.async_show_form(step_id="edit_group", data_schema=schema)

        # If form submitted from edit_group
        if user_input is not None and self._working_group_index is not None:
            groups = self._get_groups()
            idx = self._working_group_index
            group = groups[idx]
            # validate sensors matching rules:
            chosen = user_input.get("sensors", [])
            # if group type not custom, double-check chosen sensors match type
            gtype = group.get("type", "custom")
            if chosen:
                # if first sensor exists and it's custom group, enforce same type for rest
                first = chosen[0]
                first_state = self.hass.states.get(first)
                # determine first device_class/unit for restriction
                first_dc = first_state.attributes.get("device_class")
                first_unit = first_state.attributes.get("unit_of_measurement")
                # check each chosen
                for e in chosen:
                    st = self.hass.states.get(e)
                    if not st:
                        continue
                    if gtype != "custom" and not self._match_sensor_type(st, gtype):
                        return self.async_show_form(step_id="edit_group", errors={"sensors": "Selected sensors must match group type"})
                    # if group type is custom and more than one chosen, enforce same device_class as first (if exists)
                    if gtype == "custom" and first_dc:
                        if st.attributes.get("device_class") != first_dc:
                            return self.async_show_form(step_id="edit_group", errors={"sensors": "Custom group sensors must have same device_class as first sensor"})
            # save updated group details
            group["name"] = user_input.get("name", group.get("name"))
            group["aggregation"] = user_input.get("aggregation", group.get("aggregation", AGGREGATION_MODES[2]))
            group["sensors"] = chosen
            groups[idx] = group
            self._save_groups(groups)
            self._working_group_index = None
            # if done flag set, return to main
            if user_input.get("done"):
                return await self.async_step_init()
            # otherwise show edit menu again
            return await self.async_step_init()

        # fallback back to init
        return await self.async_step_init()
