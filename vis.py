from math import acos,asin,sin,cos,sqrt,pi
from objimporter import OBJImporter
from pyglet.gl import *
from vector import Vector3, Quaternion, Plane, Ray
from vis3d import *
import pyglet
from pyglet.window import key
from lighthouse import Lighthouse, Device
import random
import tween
import json
import serial
import base64
import struct

s = serial.Serial("/dev/ttyACM0", 460800, timeout=0)

win = pyglet.window.Window(vsync=True, width=1280,height=800)

t = 0

## Set up a main camera transform to offset the scene into the screen
camera_offset_transform = GLDrawTransform(pos=Vector3.k * -10)

## Set up a rotation transform to rotate the scene
scenerot_transform = camera_offset_transform.addChild()

## Set up a debug vector manager for the main scene to draw debug information
scene_vectormanager = DebugVectorManager()
scenerot_transform.addChild(scene_vectormanager)

## Set up axes display in the lower-left corner
axes_offset_transform = GLDrawTransform(pos=Vector3(-2,-1,-5))
axesrot_transform = axes_offset_transform.addChild()
axesrot_transform.shadow = scenerot_transform

axes_vectormanager = DebugVectorManager()
axesrot_transform.addChild(axes_vectormanager)

axes_vectormanager.addVector(Vector3.zero, Vector3.i * 0.5, (1,0,0,1))
axes_vectormanager.addVector(Vector3.zero, Vector3.j * 0.5, (0,1,0,1))
axes_vectormanager.addVector(Vector3.zero, Vector3.k * 0.5, (0,0,1,1))

sensor_positions = ([Vector3(4.8,0,0.3),
                     Vector3(0,0,4.0),
                     Vector3(-2.1,4.1,0.3),
                     Vector3(-2.1,-4.1,0.3)])

lighthouse = Lighthouse()
target_device = Device(sensorpos = sensor_positions, color = (0, 1, 0.5, 1))
slave_device = Device(sensorpos = sensor_positions, color = (1, 0.5, 0, 1))

scenerot_transform.addChild(lighthouse)
scenerot_transform.addChild(target_device)
scenerot_transform.addChild(slave_device)

view_rays = []
transform = vector.Matrix4x4.identity

def update_slave_sensor():
    global transform

    slave_device.pos = Vector3(*(transform.col(3)[:-1]))

    slave_device.rot = transform.rotation()

## This function updates the simulation state
def step_simulation():
    global pos_delta
    scene_vectormanager.clear()

def loop_simulation(dt):
    global slave_error

    scene_vectormanager.clear(15)
    for r in view_rays:
        scene_vectormanager.addRay(r, color=(0,0,1,1), group=15)

    update_slave_sensor()

@win.event
def on_show():
    glEnable(GL_DEPTH_TEST | GL_LIGHTING)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glShadeModel(GL_SMOOTH)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(win.width)/win.height, 0.1, 360)

def extract_data(line):
    try:
        if '^' not in line or '$' not in line:
            return [],vector.Matrix4x4.zero
        line = line[line.find('^')+1:line.find('$')]
        raw = struct.unpack('f'*(16 + 12), base64.b64decode(line))
    except Exception as e:
        print line
        return [],vector.Matrix4x4.zero

    ret_rays = [Ray(Vector3.zero,
                Vector3(*raw[16 + i * 3:16 + (i + 1) * 3]) * 10) for i in
                range(4)]

    return ret_rays,vector.Matrix4x4(*raw[:16])

readbuf = ""

@win.event
def on_draw():
    global view_rays
    global readbuf
    global transform

    readval = s.read(100)
    line = ""
    while(readval):
        readbuf += readval
        if('\n' in readbuf):
            last_newline_pos = len(readbuf) - readbuf[::-1].find('\n') - 1
            rem = readbuf[last_newline_pos + 1:]
            line = readbuf
            if('\n' in line):
                line = line[:-line[::-1].find('\n')-1]
            readbuf = rem
            break

        readval = s.read(100)
    if(line):
        view_rays,transform = extract_data(line)

    win.clear()

    glMatrixMode(GL_MODELVIEW)

    glLoadIdentity()

    glColor4f(1.0,0.0,0.0,1.0)

    camera_offset_transform.draw()
    axes_offset_transform.draw()

@win.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if buttons & pyglet.window.mouse.LEFT and not buttons & pyglet.window.mouse.RIGHT:
        scenerot_transform.rot = (
                Quaternion.fromAxisAngle(Vector3.j,
                                         float(dx) / win.width * 2 * pi) *
                Quaternion.fromAxisAngle(Vector3.i,
                                         -float(dy) / win.height * 2 * pi) *
                scenerot_transform.rot).unit()
    elif buttons & pyglet.window.mouse.RIGHT and not buttons & pyglet.window.mouse.LEFT:
        camera_offset_transform.pos += Vector3(dx,dy,0) * 0.05

@win.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    camera_offset_transform.pos += Vector3(0,0,scroll_y) * 0.5

@win.event
def on_key_press(symbol, modifiers):
    pass

def process_loop(dt):
    global t
    t += dt
    loop_simulation(dt)

pyglet.clock.schedule(process_loop)
pyglet.app.run()
