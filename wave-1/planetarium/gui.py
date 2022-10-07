#!/usr/bin/env python3

import tkinter
import turtle
import math
import random

from gravity import Body, calculate_system_energy
from initial_states import solar_bodies, n_nary_stable_system
from point import Point, Vector

SCALE = 10**9
HEX_CHARS = "0123456789ABCDEF"

options = {
    "calc_per_draw": 1,
    "run": True,
    "step_size": 10 ** 5,
    "steps": 0,
    "sim_time": 0
}
turtles = []
bodies = []


def convert_time(total_seconds: int):
    t_sec = total_seconds % 60
    t_min = total_seconds // 60
    t_h = t_min // 60
    t_min = t_min % 60
    days = t_h // 24
    t_h = t_h % 24
    years = days // 365
    days = days % 365
    return f"{years} years, {days} days, {t_h} hours, {t_min} minutes, {t_sec}, seconds"


def toggle_run():
    options['run'] = not options['run']


def full_delete(event):
    if check_toplevels():
        return

    turtles.clear()
    bodies.clear()
    turtle_screen.clear()

    options['steps'] = 0
    options['sim_time'] = 0
    options['run'] = False
    label_stats['text'] = f"step number: {options['steps']} | time elapsed: {options['sim_time']}"


def calc_up(event):
    if check_toplevels():
        return

    options['calc_per_draw'] *= 2
    settings = f"step size: {convert_time(options['step_size'])} | steps per draw: {options['calc_per_draw']}"
    label_settings['text'] = settings


def calc_down(event):
    if check_toplevels():
        return
    if options['calc_per_draw'] <= 1:
        return

    options['calc_per_draw'] = options['calc_per_draw'] // 2
    settings = f"step size: {convert_time(options['step_size'])} | steps per draw: {options['calc_per_draw']}"
    label_settings['text'] = settings


def speed_up(event):
    if check_toplevels():
        return

    options['step_size'] += int(options['step_size'] / 100 * 12)
    settings = f"step size: {convert_time(options['step_size'])} | steps per draw: {options['calc_per_draw']}"
    label_settings['text'] = settings


def speed_down(event):
    if check_toplevels():
        return

    options['step_size'] -= int(options['step_size'] / 100 * 10)
    settings = f"step size: {convert_time(options['step_size'])} | steps per draw: {options['calc_per_draw']}"
    label_settings['text'] = settings


def check_toplevels():
    for widget in window.winfo_children():
        if isinstance(widget, tkinter.Toplevel):
            return True
    return False


def rand_color():
    s = "#"
    for _ in range(6):
        s += random.choice(HEX_CHARS)
    return s


def reset_turtles(turtle_screen, turtles):
    if check_toplevels():
        return

    for t in turtles:
        t.clear()
    turtle_screen.update()


def edit_body(n_window, entries, body_to_edit):
    name, posx, posy, mass, vecx, vecy = map(lambda x: x.get(), entries)
    try:
        posx, posy, mass, vecx, vecy = map(float, (posx, posy, mass, vecx, vecy))
    except ValueError:
        print("check your values")
        return
    n_window.destroy()

    if body_to_edit is None:
        t = turtle.RawTurtle(turtle_screen)
        t.penup()
        t.goto(posx/SCALE, posy/SCALE)
        t.pendown()
        t.color(rand_color())
        turtles.append(t)
        bodies.append(Body(Point(posx, posy), mass, Vector(vecx, vecy), name))
    else:
        body_to_edit.name = name
        body_to_edit.location.x = posx
        body_to_edit.location.y = posy
        body_to_edit.mass = mass
        body_to_edit.motion_vector.x = vecx
        body_to_edit.motion_vector.y = vecy


def body_prompt(x, y):
    # build new window
    n_window = tkinter.Toplevel(window)
    n_window.title("Add body")

    l_name = tkinter.Label(n_window, text="Name")
    l_name.pack()
    e_name = tkinter.Entry(n_window)
    e_name.pack()
    l_posx = tkinter.Label(n_window, text="Location X")
    l_posx.pack()
    e_posx = tkinter.Entry(n_window)
    e_posx.pack()
    l_posy = tkinter.Label(n_window, text="Location Y")
    l_posy.pack()
    e_posy = tkinter.Entry(n_window)
    e_posy.pack()
    l_mass = tkinter.Label(n_window, text="Mass")
    l_mass.pack()
    e_mass = tkinter.Entry(n_window)
    e_mass.pack()
    l_vecx = tkinter.Label(n_window, text="Vector X")
    l_vecx.pack()
    e_vecx = tkinter.Entry(n_window)
    e_vecx.pack()
    l_vecy = tkinter.Label(n_window, text="Vector Y")
    l_vecy.pack()
    e_vecy = tkinter.Entry(n_window)
    e_vecy.pack()

    # if body was clicked, load data from it
    body_to_edit = None
    for body in bodies:
        if body.location.x / SCALE + 395 < x < body.location.x / SCALE + 405:
            if body.location.y / SCALE * -1 + 395 < y < body.location.y / SCALE * -1 + 405:
                body_to_edit = body
                e_name.insert(0, str(body.name))
                e_posx.insert(0, str(body.location.x))
                e_posy.insert(0, str(body.location.y))
                e_mass.insert(0, str(body.mass))
                e_vecx.insert(0, str(body.motion_vector.x))
                e_vecy.insert(0, str(body.motion_vector.y))
                break

    if body_to_edit is None:
        e_posx.insert(0, str((x - 400) * SCALE))
        e_posy.insert(0, str((y - 400) * -1 * SCALE))

    entries = (e_name, e_posx, e_posy, e_mass, e_vecx, e_vecy)
    btn_submit = tkinter.Button(n_window,
                                text="ok",
                                command=lambda:
                                edit_body(n_window, entries, body_to_edit))
    btn_submit.pack()


def tick():
    if not options['run']:
        return
    # for body in bodies:
    #     print(body)
    for i in range(options['calc_per_draw']):
        for i in range(len(bodies)):
            body = bodies[i]
            t = turtles[i]
            body.acceleration(bodies, options['step_size'])
            body.update_pos(options['step_size'])
            t.right(t.heading() - math.degrees(math.atan2(body.motion_vector.y, body.motion_vector.x)))
        options['steps'] += 1
        options['sim_time'] += options['step_size']

    for i in range(len(bodies)):
        body = bodies[i]
        t = turtles[i]
        t.goto(body.location.x/SCALE, body.location.y/SCALE)

    label_stats['text'] = f"step number: {options['steps']} | time elapsed: {convert_time(options['sim_time'])}"
    turtle_screen.update()


if __name__ == '__main__':
    # build main window
    window = tkinter.Tk()
    # bodies = n_nary_stable_system(3, scale=SCALE, screen_size=(800, 800))
    bodies = solar_bodies(only_first_n_planets=4)

    can = tkinter.Canvas(window, width=800, height=800)
    can.pack()
    turtle_screen = turtle.TurtleScreen(can)
    turtle_screen.tracer(0,0)
    stats = f"step number: {options['steps']} | time elapsed: {options['sim_time']}"
    label_stats = tkinter.Label(window, text=stats)
    label_stats.pack()
    settings = f"step size: {convert_time(options['step_size'])} | steps per draw: {options['calc_per_draw']}"
    label_settings = tkinter.Label(window, text=settings)
    label_settings.pack()
    t_mouse = "click on canvas to create new body, or click existing one (tip of turtle) to edit it"
    label_mouse = tkinter.Label(window, text=t_mouse)
    label_mouse.pack()
    t_keybinds = "SPACE: play/pause | R: reset trails | C: remove bodies and lines | Q/E: step size up/down | A/D: calculations per update"
    label_keybinds = tkinter.Label(window, text=t_keybinds)
    label_keybinds.pack()

    turtles = []
    for i in bodies:
        t = turtle.RawTurtle(turtle_screen)
        t.penup()
        t.goto(i.location.x/SCALE, i.location.y/SCALE)
        t.pendown()
        t.color(rand_color())
        turtles.append(t)

    # bindings for keyboard and mouse
    can.bind("<Button-1>", lambda event: body_prompt(event.x, event.y))
    can.bind_all("r", lambda x: reset_turtles(turtle_screen, turtles))
    can.bind_all("<space>", lambda x: toggle_run())
    can.bind_all("e", speed_up)
    can.bind_all("q", speed_down)
    can.bind_all("c", full_delete)
    can.bind_all("d", calc_up)
    can.bind_all("a", calc_down)

    while True:
        tick()
        window.after(1)
        window.update()
