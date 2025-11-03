from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HA_Narodmon_Status(coordinator)], update_before_add=True)

class HA_Narodmon_Status(Entity):
    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "HA Narodmon Sender Status"
        self._attr_unique_id = "ha_narodmon_sender_status"
        self._state = "idle"

    @property
    def state(self):
        return self._state

    async def async_update(self):
        await self._coordinator.async_refresh()
        parts = []
        for k, buf in list(self._coordinator.buffers.items()):
            if buf:
                parts.append(f"{k}:{buf[-1][1]:.2f}")
        if parts:
            self._state = ", ".join(parts)
        else:
            self._state = "no data"
