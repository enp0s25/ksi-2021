#!/usr/bin/env python3

from enum import Enum
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict


class DeviceType(Enum):
    PLUG = "SmartPlug"
    LIGHT = "SmartLight"
    RADIATOR = "SmartRadiator"
    TEMPERATURE = "TemperatureSensor"
    SWITCH = "SwitchSensor"
    MOTION = "MotionSensor"

@dataclass_json
@dataclass
class GenericDevice:
    id: str
    notes: str
    actions: Dict[str, str]

@dataclass_json
@dataclass
class DeviceWithOnOffTracking(GenericDevice):
    current_state: bool
    power_usage_last_recalculated: int
    power_usage: int
    power_usage_coefficient: int


@dataclass
class SmartPlug(DeviceWithOnOffTracking):
    type: DeviceType = DeviceType.PLUG


@dataclass
class SmartLight(DeviceWithOnOffTracking):
    color_temperature: int
    type: DeviceType = DeviceType.LIGHT


@dataclass
class SmartRadiator(DeviceWithOnOffTracking):
    type: DeviceType = DeviceType.RADIATOR


@dataclass
class TemperatureSensor(GenericDevice):
    temperature: float
    type: DeviceType = DeviceType.TEMPERATURE



@dataclass
class MotionSensor(GenericDevice):
    collector_url: str
    last_triggered_timestamp: int
    type: DeviceType = DeviceType.MOTION


@dataclass
class SwitchSensor(DeviceWithOnOffTracking):
    collector_url: str
    type: DeviceType = DeviceType.SWITCH


if __name__ == "__main __":
    print("can't be run as main")
    exit()