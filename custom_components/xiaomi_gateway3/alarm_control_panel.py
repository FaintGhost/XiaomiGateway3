import logging

from homeassistant.components.alarm_control_panel import \
    SUPPORT_ALARM_ARM_AWAY, SUPPORT_ALARM_ARM_HOME, SUPPORT_ALARM_ARM_NIGHT, \
    SUPPORT_ALARM_TRIGGER, AlarmControlPanelEntity
from homeassistant.const import STATE_ALARM_ARMED_AWAY, \
    STATE_ALARM_ARMED_HOME, STATE_ALARM_ARMED_NIGHT, STATE_ALARM_DISARMED, \
    STATE_ALARM_TRIGGERED
from homeassistant.core import callback

from . import DOMAIN
from .core.converters import Converter
from .core.device import XDevice, XEntity
from .core.gateway import XGateway

_LOGGER = logging.getLogger(__name__)

ALARM_STATES = [STATE_ALARM_DISARMED, STATE_ALARM_ARMED_HOME,
                STATE_ALARM_ARMED_AWAY, STATE_ALARM_ARMED_NIGHT]


async def async_setup_entry(hass, config_entry, async_add_entities):
    def setup(gateway: XGateway, device: XDevice, conv: Converter):
        async_add_entities([XiaomiAlarm(gateway, device, conv)])

    gw: XGateway = hass.data[DOMAIN][config_entry.entry_id]
    gw.add_setup(__name__, setup)


# noinspection PyAbstractClass
class XiaomiAlarm(XEntity, AlarmControlPanelEntity):
    @property
    def supported_features(self):
        return (SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY |
                SUPPORT_ALARM_ARM_NIGHT | SUPPORT_ALARM_TRIGGER)

    @property
    def code_arm_required(self):
        return False

    @callback
    def async_set_state(self, data: dict):
        if self.attr in data:
            self._attr_state = data[self.attr]
        if data.get("alarm_trigger") is True:
            self._attr_state = STATE_ALARM_TRIGGERED

    async def async_alarm_disarm(self, code=None):
        await self.device_send({self.attr: "disarmed"})

    async def async_alarm_arm_home(self, code=None):
        await self.device_send({self.attr: "armed_home"})

    async def async_alarm_arm_away(self, code=None):
        await self.device_send({self.attr: "armed_away"})

    async def async_alarm_arm_night(self, code=None):
        await self.device_send({self.attr: "armed_night"})

    async def async_alarm_trigger(self, code=None):
        await self.device_send({"alarm_trigger": True})

    async def async_update(self):
        # we should not call write_ha_state from async_update function
        await self.device_read(self.subscribed_attrs)
