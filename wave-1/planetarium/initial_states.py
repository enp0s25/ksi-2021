import math
from typing import Tuple, List
import json
import string

from point import Point, Vector
from gravity import Body


def solar_bodies(only_first_n_planets: int = 4) -> List[Body]:
    # https://devstronomy.com/#/datasets
    with open('planets.json') as f:
        content = json.load(f)

    bodies = [Body(Point(0, 0), 1.989 * (10**30), Vector(0, 0), "Sun")]

    for x in content:
        if int(x["id"]) > only_first_n_planets:
            continue

        distance_from_sun = x["distanceFromSun"] * 10**9  # meters
        mass = x["mass"] * 10**24  # kg
        orbital_velocity = x["orbitalVelocity"] * 10**3  # meters per second

        bodies.append(
            Body(
                Point(distance_from_sun, 0),
                mass,
                Vector(0, orbital_velocity),
                x["name"]
            )
        )
    return bodies


def n_nary_stable_system(n_stars: int = 3, scale=10**9, screen_size: Tuple[int, int] = (400, 300)) -> List[Body]:
    screensize_max = max(screen_size)

    bodies = []
    circle_radius = int(screensize_max * 0.4) * scale

    for i in range(n_stars):
        angle_degrees = 360/n_stars * i
        angle_radians = math.radians(angle_degrees)

        x_circle_1 = math.cos(angle_radians)
        y_circle_1 = math.sin(angle_radians)

        bodies.append(
            Body(
                Point(x_circle_1 * circle_radius, y_circle_1 * circle_radius),
                10**24,
                Vector(y_circle_1 * n_stars * 2, -x_circle_1 * n_stars * 2),
                string.ascii_uppercase[i]
            )
        )
    return bodies
