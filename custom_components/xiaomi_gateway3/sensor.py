import asyncio
import logging
from asyncio import Task
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN
from .core.converters import Converter
from .core.device import XDevice, XEntity
from .core.gateway import XGateway

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass, entry, add_entities):
    def setup(gateway: XGateway, device: XDevice, conv: Converter):
        cls = XiaomiAction if conv.attr == "action" else XiaomiSensor
        add_entities([cls(gateway, device, conv)])

    gw: XGateway = hass.data[DOMAIN][entry.entry_id]
    gw.add_setup(__name__, setup)


class XiaomiSensor(XEntity, SensorEntity, RestoreEntity):
    @callback
    def async_set_state(self, data: dict):
        if self.attr in data:
            self._attr_state = data[self.attr]
        for k, v in data.items():
            if k in self.subscribed_attrs and k != self.attr:
                self._attr_extra_state_attributes[k] = v

    @callback
    def async_restore_last_state(self, state: str, attrs: dict):
        """Restore previous state."""
        self._attr_state = state
        for k, v in attrs.items():
            if k in self.subscribed_attrs:
                self._attr_extra_state_attributes[k] = v

    async def async_update(self):
        await self.device_read(self.subscribed_attrs)


class XiaomiAction(XEntity):
    _attr_state = ""
    _combined_attrs: dict = None
    _clear_task: Task = None

    @property
    def extra_state_attributes(self):
        return self._combined_attrs or self._attr_extra_state_attributes

    async def async_clear_state(self):
        await asyncio.sleep(.3)

        self._attr_state = ""
        self.async_write_ha_state()

    @callback
    def async_set_state(self, data: dict):
        if self._clear_task:
            self._clear_task.cancel()

        self._attr_state = data[self.attr]
        self._combined_attrs = {**self._attr_extra_state_attributes, **data}

        # repeat event from Aqara integration
        self.hass.bus.async_fire("xiaomi_aqara.click", {
            "entity_id": self.entity_id, "click_type": self._attr_state
        })

        self._clear_task = self.hass.async_create_task(self.async_clear_state())
