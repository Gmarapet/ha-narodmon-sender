import asyncio, logging
from datetime import datetime, timedelta
from collections import deque, defaultdict

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.components import persistent_notification

from .const import (
    DOMAIN, CONF_MAC, CONF_INTERVAL, CONF_GROUPS, CONF_CUSTOM,
    CONF_LATITUDE, CONF_LONGITUDE, CONF_ELEVATION,
    DEFAULT_INTERVAL, SAMPLE_INTERVAL, MAX_BUFFER_MULTIPLIER, API_BASE, SUPPORTED_GROUPS
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    mac = entry.data.get(CONF_MAC)
    interval = entry.data.get(CONF_INTERVAL, DEFAULT_INTERVAL)
    groups = entry.data.get(CONF_GROUPS, [])
    customs = entry.data.get(CONF_CUSTOM, [])
    latitude = entry.data.get(CONF_LATITUDE, hass.config.latitude)
    longitude = entry.data.get(CONF_LONGITUDE, hass.config.longitude)
    elevation = entry.data.get(CONF_ELEVATION, getattr(hass.config, "elevation", 0.0))

    coordinator = NarodmonCoordinator(hass, mac, groups, customs, interval, latitude, longitude, elevation)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    coordinator.start_sampling_task()
    await coordinator.async_refresh()
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.stop_sampling_task()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class NarodmonCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, mac, groups, customs, interval, latitude, longitude, elevation):
        super().__init__(
            hass,
            _LOGGER,
            name="HA Narodmon Sender Coordinator",
            update_interval=timedelta(seconds=interval),
        )
        self.hass = hass
        self.mac = mac
        self.groups = groups or []
        self.customs = customs or []
        self.interval = interval
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation

        self.buffers = defaultdict(lambda: deque())
        self._maxlen = max(1, int((self.interval / SAMPLE_INTERVAL) * MAX_BUFFER_MULTIPLIER))
        self._sampling_task = None
        self._stopping = False
        self.notified_groups = set()

    def _aggregate_values(self, values, mode):
        if not values:
            return None
        if mode == "average":
            return sum(values) / len(values)
        elif mode == "minimum" or mode == "min":
            return min(values)
        elif mode == "maximum" or mode == "max":
            return max(values)
        return None

    async def _notify_group_failure(self, group_name: str, reason: str):
        if group_name not in self.notified_groups:
            self.notified_groups.add(group_name)
            message = f"❗ Group **{group_name}** has no valid sensors to send. Reason: {reason}"
            await persistent_notification.async_create(self.hass, message, title="HA Narodmon Sender: group failure", notification_id=f"ha_narodmon_{group_name}")
            _LOGGER.warning("Group %s excluded: %s", group_name, reason)

    async def _clear_group_notification(self, group_name: str):
        if group_name in self.notified_groups:
            notif_id = f"ha_narodmon_{group_name}"
            try:
                await persistent_notification.async_dismiss(self.hass, notif_id)
            except Exception:
                try:
                    persistent_notification.async_dismiss(self.hass, notif_id)
                except Exception:
                    pass
            self.notified_groups.discard(group_name)
            _LOGGER.info("Group %s recovered — notification removed", group_name)

    def start_sampling_task(self):
        if self._sampling_task is None:
            self._stopping = False
            self._sampling_task = asyncio.create_task(self._sampling_loop())
            _LOGGER.debug("Started sampling task for HA Narodmon Sender")

    async def stop_sampling_task(self):
        if self._sampling_task:
            self._stopping = True
            self._sampling_task.cancel()
            try:
                await self._sampling_task
            except asyncio.CancelledError:
                pass
            self._sampling_task = None
            _LOGGER.debug("Stopped sampling task for HA Narodmon Sender")

    async def _sampling_loop(self):
        try:
            while not self._stopping:
                ts = datetime.utcnow().timestamp()
                # sample each group
                for g in self.groups:
                    group_key = g.get("group_key") or g.get("name") or "unknown"
                    sensors = g.get("sensors", [])
                    agg = g.get("aggregation", "average")
                    values = []
                    for entity_id in sensors:
                        state = self.hass.states.get(entity_id)
                        if not state:
                            continue
                        raw = state.state
                        if raw in (None, "", "unknown", "unavailable"):
                            continue
                        try:
                            values.append(float(raw))
                        except Exception:
                            continue
                    if values:
                        agg_value = self._aggregate_values(values, agg)
                        buf = self.buffers[group_key]
                        # bounded buffer
                        if len(buf) >= self._maxlen:
                            buf.popleft()
                        buf.append((ts, agg_value))
                        await self._clear_group_notification(group_key)
                    else:
                        await self._notify_group_failure(group_key, "no valid sensors")

                # custom sensors
                for c in self.customs:
                    identifier = c.get("identifier") or c.get("name") or "custom"
                    sensors = c.get("sensors", [])
                    values = []
                    for entity_id in sensors:
                        state = self.hass.states.get(entity_id)
                        if not state:
                            continue
                        raw = state.state
                        if raw in (None, "", "unknown", "unavailable"):
                            continue
                        try:
                            values.append(float(raw))
                        except Exception:
                            continue
                    if values:
                        agg_value = sum(values)/len(values)
                        buf = self.buffers[identifier]
                        if len(buf) >= self._maxlen:
                            buf.popleft()
                        buf.append((ts, agg_value))
                        await self._clear_group_notification(identifier)
                    else:
                        await self._notify_group_failure(identifier, "no valid sensors")

                # cleanup old entries beyond interval (prevent memory growth)
                cutoff = datetime.utcnow().timestamp() - self.interval
                for key, buf in list(self.buffers.items()):
                    # remove left while older than cutoff
                    while buf and buf[0][0] < cutoff:
                        buf.popleft()
                    # if buffer empty and not recently used, remove to free memory
                    if not buf:
                        try:
                            del self.buffers[key]
                        except KeyError:
                            pass

                await asyncio.sleep(SAMPLE_INTERVAL)
        except asyncio.CancelledError:
            _LOGGER.debug("Sampling task cancelled")
            return
        except Exception as e:
            _LOGGER.exception("Unexpected error in sampling loop: %s", e)
