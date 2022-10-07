#!/usr/bin/env python3


import os
import json
import requests

import devices as devs

from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta
from datetime import time as dt_time
from functools import wraps

from flask import Flask, request, session, redirect, abort
from flask.helpers import url_for
from flask.templating import render_template


app = Flask("Smart Home", template_folder="templates")
app.secret_key = os.urandom(16).hex()

# since only these users are using the app there is no need for registration
# and "credentials" can be hardcoded, I left them plain-text instead of hashed
# to improve readability of source code
users = {
    "karlik": "asdf",
    "sob_karsob": "asdf",
    "los_karlos": "asdf",
    "zelvicka_julie": "asdf"
}
# these rooms can be accessed by everyone
global_rooms = ["kuchyna", "obyvak", "koupelna"]

# hours, minutes
# didn't have time to make it calculate sunrise time based on day of year
SUNRISE_START = dt_time(5, 0)
SUNSET_START = dt_time(16, 0)


def load_devices(filename: str) -> Dict[str, Dict[str, Any]]:
    """
    load device configurations from file, create if not found
    """

    if not os.path.exists(filename):
        print(f"Couldn't find device file {filename}, generating devices now")
        import device_setup
        device_setup.generate(filename)
    with open(filename, "r") as f:
        dev_config = json.load(f)
        f.close()
    devices = dev_config['devices']
    for device in devices.keys():
        if devices[device]['type'] == "MotionSensor":
            devices[device] = devs.MotionSensor.from_dict(devices[device])
        elif devices[device]['type'] == "SmartLight":
            devices[device] = devs.SmartLight.from_dict(devices[device])
        elif devices[device]['type'] == "SwitchSensor":
            devices[device] = devs.SwitchSensor.from_dict(devices[device])
    return dev_config


def get_status(device: Any) -> Any:
    """
    update device
    """

    resp = requests.get(device.actions['device_info'])
    j = resp.content.decode('utf-8')

    if device.type == devs.DeviceType.LIGHT:
        return devs.SmartLight.from_json(j)
    elif device.type == devs.DeviceType.MOTION:
        return devs.MotionSensor.from_json(j)
    elif device.type == devs.DeviceType.SWITCH:
        return devs.SwitchSensor.from_json(j)

def check_perms(device: Any, user: str) -> bool:
    if device.id in device_config['rooms'][user].values():
        return True
    for room in global_rooms:
        if device.id in device_config['rooms'][room].values():
            return True
    return False

def get_private_lights() -> List[Tuple[str, Any]]:
    """
    return lights from private rooms
    """

    lights: List[Tuple[str, Any]] = []
    for user in users.keys():
        light_id = device_config['rooms'][user]['SmartLight']
        light = device_config['devices'][light_id]
        lights.append((user, light))
    return lights

def calc_heating() -> List[Tuple[str, int, int]]:
    """
    calculate how much % of heating bill should each person pay

    returns list of tuples (user, percent, energy_used)
    """

    energy_total = 0
    l: List[Tuple[str, int]] = []
    for user, light in get_private_lights():
        # no need to refresh devices, it is done before rendering template
        energy_last = None
        if light.notes != "":
            energy_last = json.loads(light.notes).get('energy_last')
        if energy_last is None:
            energy_last = 0
        energy = light.power_usage - energy_last
        energy_total += energy
        l.append((user, energy))
    out_l: List[Tuple[str, int]] = []
    for user, energy in l:
        if energy_total == 0:
            bill = 0
        else:
            bill = energy / energy_total * 100
        out_l.append((user, bill, energy))
    return out_l

def set_light_temp(temp: int) -> None:
    """
    set temperature of all lights to temp
    """

    for room in device_config['rooms'].values():
        light = device_config['devices'][room['SmartLight']]
        ntemp_url = light.actions["device_info"]
        ntemp_url += f"/color_temperature/{str(temp)}"
        resp = requests.get(ntemp_url)
        j = resp.content.decode("utf-8")
        new_light = devs.SmartLight.from_json(j)
        device_config['devices'][room['SmartLight']] = new_light

device_config = load_devices("device_config.json")

def login_requred(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap


@app.route("/")
@app.route("/dashboard")
@login_requred
def dashboard():
    # this takes quite long to load
    # refreshing device status would be a bit faster irl with use of asyncio
    # or other library that would allow polling all devices at once
    for device in device_config['devices'].values():
        device_config['devices'][device.id] = get_status(device)
    current_time = int(datetime.now().timestamp())
    return render_template("dashboard.html",
                           device_config=device_config,
                           dtypes=devs.DeviceType,
                           check_perms=check_perms,
                           timedelta=timedelta,
                           current_time=current_time,
                           calc_heating=calc_heating)


@app.route('/cron')
def cron():
    # used to set color temperature of lights
    # there is no point in running it more than once per minute

    current_time = datetime.now().time()
    m_current = current_time.hour * 60 + current_time.minute
    m_sunrise_start = SUNRISE_START.hour * 60 + SUNRISE_START.minute
    m_sunset_start = SUNSET_START.hour * 60 + SUNSET_START.minute

    # calculate current temperature
    if m_sunrise_start < m_current < m_sunrise_start + 90:
        temp = 2300 + (m_current - m_sunrise_start) * 46
    elif m_sunset_start < m_current < m_sunset_start + 90:
        temp = 6500 - (m_current - m_sunset_start) * 46
    elif  m_sunrise_start + 90 < m_current < m_sunset_start:
        temp = 6500
    elif  m_sunset_start + 90 < m_current or m_current < m_sunrise_start:
        temp = 2300

    # get random light and see if temperature matches
    random_light_id = list(device_config['rooms'].values())[0]['SmartLight']
    random_light = device_config['devices'][random_light_id]
    # if temperature does not match, set all lights to new temperature
    if random_light.color_temperature != temp:
        set_light_temp(temp)
    return ""

@app.route('/pay_heating_bill')
@login_requred
def pay_heating_bill():
    """
    resets heating bill calculations
    """
    for user, light in get_private_lights():
        print(user)
        energy_last = None
        if light.notes != "":
            energy_last = json.loads(light.notes).get('energy_last')
            print(energy_last)
        if energy_last is None:
            energy_last = 0
        new_energy_data = '{"energy_last": ' + str(light.power_usage) + '}'
        # save power_used at reset to smart light notes
        requests.post(light.actions['set_notes_POST'], data=new_energy_data)
    return ""



@app.route("/device/<device_id>")
@login_requred
def device_info(device_id: str):
    device = device_config['devices'].get(device_id)
    if device is None:
        abort(404)
    resp = requests.get(device.actions['device_info'])
    j = resp.content.decode('utf-8')

    if device.type == devs.DeviceType.LIGHT:
        new_device = devs.SmartLight.from_json(j)
    elif device.type == devs.DeviceType.MOTION:
        new_device = devs.MotionSensor.from_json(j)
    elif device.type == devs.DeviceType.SWITCH:
        new_device = devs.SwitchSensor.from_json(j)

    current_time = int(datetime.now().timestamp())
    return render_template("device.html",
                           device=new_device.to_dict(),
                           timedelta=timedelta,
                           current_time=current_time)


@app.route("/device/<device_id>/toggle")
@login_requred
def toggle(device_id: str):
    device = device_config['devices'].get(device_id)
    if device is None:
        abort(404)
    if check_perms(device, session['user']):
        if device.actions.get('toggle_state') is not None:
            requests.get(device.actions['toggle_state'])
        else:
            abort(400)
    else:
        abort(401)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    elif request.method == "POST":
        username = request.form.get('username')
        passwd = request.form.get('pass')
        if users.get(username) is not None and users.get(username) == passwd:
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")


@app.route("/logout")
@login_requred
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route('/map')
@login_requred
def flat_map():
    lights: Dict[str, Any] = {}
    for room in device_config['rooms'].keys():
        light_id = device_config['rooms'][room]['SmartLight']
        light = device_config['devices'][light_id]
        resp = requests.get(light.actions['device_info'])
        j = resp.content.decode("utf-8")
        new_light = devs.SmartLight.from_json(j)
        device_config['devices'][light_id] = new_light
        lights[room] = new_light
    return render_template("flat_map.html", lights=lights)


if __name__ == "__main__":
    app.run(debug=True)