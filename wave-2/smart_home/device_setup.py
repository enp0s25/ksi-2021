#!/usr/bin/env python3

import requests
import json

import devices as dev

from typing import Any, Dict
from time import sleep
from urllib.parse import quote_plus

# this script can be used to generate devices and save them to json config file


URL = "https://home_automation.iamroot.eu/"

rooms = {
    "kuchyna": ["MotionSensor", "SmartLight", "SwitchSensor"],
    "obyvak": ["MotionSensor", "SmartLight", "SwitchSensor"],
    "koupelna": ["SmartLight", "SwitchSensor"],
    "karlik": ["SmartLight", "SwitchSensor"],
    "sob_karsob": ["SmartLight", "SwitchSensor"],
    "los_karlos": ["SmartLight", "SwitchSensor"],
    "zelvicka_julie": ["SmartLight", "SwitchSensor"]
}

device_config: Dict[str, Dict[str, Any]] = {
    "devices": {},
    "rooms": {}
}

def mk_device(dev_type: dev.DeviceType) -> Any:
    """
    create new device
    """

    sleep(0.2)
    resp = requests.get(f"{URL}new{dev_type}")
    j = resp.content.decode('utf-8')
    if dev_type == dev.DeviceType.LIGHT.value:
        return dev.SmartLight.from_json(j)
    elif dev_type == dev.DeviceType.MOTION.value:
        return dev.MotionSensor.from_json(j)
    elif dev_type == dev.DeviceType.SWITCH.value:
        return dev.SwitchSensor.from_json(j)

def setup_room(room: Dict[str, str], devices: Dict[str, Any]) -> None:
    """
    Link switches and motion sensors in room to control light
    """

    light = devices[room['SmartLight']]
    light_on = quote_plus(light.actions['turn_on'])
    light_toggle = quote_plus(light.actions['toggle_state'])

    ss = devices[room['SwitchSensor']]
    ss_new_collector = f"{URL}/device/{ss.id}/report_url?url={light_toggle}"
    requests.get(ss_new_collector)
    ss.collector_url = light.actions["toggle_state"]
    ss.actions["change_report_url"] = ss_new_collector
    if room.get('MotionSensor') is not None:
        ms = devices[room.get('MotionSensor')]
        ms_new_collector = f"{URL}/device/{ms.id}/report_url?url={light_on}"
        requests.get(ms_new_collector)
        ms.collector_url = light.actions["turn_on"]
        ms.actions["change_report_url"] = ms_new_collector

def generate(filename: str) -> None:
    """
    generate device configuration and save it as filename
    """
    for room in rooms.keys():
        room_device_ids = {}
        room_devices = {}
        for new_device in rooms[room]:
            device = mk_device(new_device)
            room_device_ids[new_device] = device.id
            room_devices[device.id] = device
            print(f"{room}: {new_device}")
        print(room_device_ids)

        setup_room(room_device_ids, room_devices)

        for device in room_devices.values():
            # dump device as JSON and load it again as dictionary
            # device.to_dict() wouldn't change nested things like DeviceType
            # to objects that json.dump() can serialize
            device_config['devices'][device.id] = json.loads(device.to_json())
        device_config['rooms'][room] = room_device_ids


    with open(filename, "w") as f:
        json.dump(device_config, f)
        f.close()

if __name__ == "__main__":
    generate("device_config.json")