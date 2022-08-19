"""Demo fan platform that has a fake fan."""
from __future__ import annotations

import logging
from operator import truediv
from re import S
from typing import Any,Optional, List
from .ds_air_service.ctrl_enum import EnumControl

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .ds_air_service.dao import Ventilation, VentilationStatus
from .ds_air_service.service import Service

PRESET_MODE_AUTO = "auto"
PRESET_MODE_SMART = "smart"
PRESET_MODE_SLEEP = "sleep"
PRESET_MODE_ON = "on"

FULL_SUPPORT = (
    FanEntityFeature.SET_SPEED | FanEntityFeature.OSCILLATE | FanEntityFeature.DIRECTION
)
LIMITED_SUPPORT = FanEntityFeature.SET_SPEED

_LOGGER = logging.getLogger(__name__)

def _log(s: str):
    s = str(s)
    for i in s.split("\n"):
        _LOGGER.debug(i)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = []
    for vent in Service.get_ventilations():
        entities.append(DsVent(vent))
    async_add_entities(entities)


class DsVent(FanEntity):
    """A demonstration fan component that uses legacy fan speeds."""

    def __init__(self, vent: Ventilation):
        _log('create ventilation:')
        _log(str(vent.__dict__))
        _log(str(vent.switch))
        """Initialize the climate device."""
        self._name = vent.alias
        self._device_info = vent
        self._unique_id = vent.unique_id
        self._switch = vent.switch 
        from .ds_air_service.service import Service
        Service.register_vent_hook(vent, self._status_change_hook)

    def _status_change_hook(self, **kwargs):
        _log('hook:')
        if kwargs.get('vent') is not None:
            vent: Ventilation = kwargs['vent']
            self._device_info = vent
            self._switch = vent.switch

        if kwargs.get('status') is not None:
            new_status: VentilationStatus = kwargs['status']
            if new_status.switch is not None:
                self._switch =  new_status.switch
        self.schedule_update_ha_state()

    @property
    def unique_id(self) -> str:
        """Return the unique id."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Get entity name."""
        return self._name

    @property
    def should_poll(self) -> bool:
        """No polling needed for a demo fan."""
        return False

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return 0

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": "新风%s" % self._name,
            "manufacturer": "DAIKIN INDUSTRIES, Ltd."
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self._switch == EnumControl.Switch.ON

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on the fan."""
        from .ds_air_service.service import Service
        Service.control_vent(self._device_info, True)
        # self._switch = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        from .ds_air_service.service import Service
        Service.control_vent(self._device_info, False)
        # self._switch = False
        self.schedule_update_ha_state()