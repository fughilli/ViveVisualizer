from math import acos,asin,sin,cos,sqrt,pi
from objimporter import OBJImporter
from pyglet.gl import *
from vector import Vector3, Quaternion
from vis3d import *
import pyglet
from pyglet.window import key

win = pyglet.window.Window(width=1280,height=800)

t = 0

## Set up a main camera transform to offset the scene into the screen
camera_offset_transform = GLDrawTransform(pos=Vector3.k * -10)

## Set up a rotation transform to rotate the scene
scenerot_transform = camera_offset_transform.addChild()

## Import a cube model and add it to the scene
cube = OBJObject()
cube.imp('box.obj')
scenerot_transform.addChild(cube)

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

pos_delta = Vector3.zero

## This function updates the simulation state
def step_simulation():
    global pos_delta
    scene_vectormanager.clear()
    cube.pos += pos_delta
    pos_delta = Vector3.random().unit() * 5
    scene_vectormanager.addVector(cube.pos, pos_delta, (1, 1, 0, 1))

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
    global world_transform
    scenerot_transform.rot = (
            Quaternion.fromAxisAngle(Vector3.j,
                                     float(dx) / win.width * 2 * pi) *
            Quaternion.fromAxisAngle(Vector3.i,
                                     -float(dy) / win.height * 2 * pi) *
            scenerot_transform.rot).unit()

@win.event
def on_key_press(symbol, modifiers):
    if(symbol == key.N):
        step_simulation()

def process_loop(dt):
    global t
    t += dt
    pass

pyglet.clock.schedule(process_loop)
pyglet.app.run()
