import bpy
import random as r
from math import radians, sin, cos, tan

MAX_LIGHTS = 3 
MIN_STRENGTH = 500
MAX_STRENGTH = 2000
MIN_RADIUS = 3
MAX_RADIUS = 10

def create_point_light(pos, strength):
    bpy.ops.object.light_add(type="POINT", location=pos)
    light = bpy.context.active_object
    light_data = bpy.data.lights[light.name]
    light_data.energy = strength            # default: 1000
    # light_data.color = (1.0, 1.0, 1.0)    # default: (1.0, 1.0, 1.0)
    # light_data.radius = 0.1               # default: 0.1
    return light

def set_position_polar_coords(obj, radius, angle_h, angle_v):
    x = radius * sin(angle_v) * cos(angle_h)
    y = radius * sin(angle_v) * sin(angle_h)
    z = radius * cos(angle_v)
    obj.location = (x, y, z)
    # light_position = (4, 1, 5.9)
    return (x, y, z)


for l in range(r.randint(1, MAX_LIGHTS)):
    strength = r.randint(MIN_STRENGTH, MAX_STRENGTH)
    light = create_point_light((0, 0, 0), strength)
    radius = r.randint(MIN_RADIUS, MAX_RADIUS)
    angle_h = radians(360 * r.random())
    angle_v = radians(90 * r.random())
    set_position_polar_coords(light, radius, angle_h, angle_v)