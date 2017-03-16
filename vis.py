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

win = pyglet.window.Window(vsync=True, width=1280,height=800)

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

lighthouse = Lighthouse()

scenerot_transform.addChild(lighthouse)

states = []
state_index = 0
auto = False

def auto_toggle():
    global auto
    auto = not auto

## This function updates the simulation state
def next_state():
    global state_index

    curstate = ""
    if(state_index < len(states)):
        curstate = states[state_index]
        state_index += 1
    else:
        curstate = states[0]
        state_index = 0
        print "Starting over..."

    cos,cs,tos,ts = curstate.split(';')

    def vstov(vs):
        return Vector3(*[float(s) for s in vs[1:-1].split(',')])

    co = vstov(cos)
    to = vstov(tos)
    cd = [vstov(vs) for vs in cs.split(':')]
    td = [vstov(vs) for vs in ts.split(':')]

    scene_vectormanager.clear()

    for cv in cd:
        scene_vectormanager.addVector(co, cv-co, (1,0,0,1), 1)
    for tv in td:
        scene_vectormanager.addVector(to, tv-to, (0,1,0,1), 2)

def loop_simulation(dt):
    if(auto):
        next_state()

@win.event
def on_show():
    glEnable(GL_DEPTH_TEST | GL_LIGHTING)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glShadeModel(GL_SMOOTH)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, float(win.width)/win.height, 0.1, 360)

@win.event
def on_draw():
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
    if(symbol == key.N):
        next_state()

    if(symbol == key.A):
        auto_toggle()

def process_loop(dt):

    loop_simulation(dt)
    pass

states = [line.strip() for line in open("states.txt").readlines()]
pyglet.clock.schedule(process_loop)
pyglet.app.run()
