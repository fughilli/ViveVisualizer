from math import acos,asin,sin,cos,sqrt,pi
from objimporter import OBJImporter
from pyglet.gl import *
from vector import Vector3, Quaternion
from vis3d import *
import pyglet
from pyglet.window import key

win = pyglet.window.Window(width=1280,height=800)

t = 0

axes_offset_transform = GLDrawTransform(pos=Vector3(-2,-1,-5))
camera_offset_transform = GLDrawTransform(pos=Vector3.k * -10)
scenerot_transform = camera_offset_transform.addChild()
axesrot_transform = axes_offset_transform.addChild()
axesrot_transform.shadow = scenerot_transform

cube = OBJObject()
cube.imp('box.obj')

dvec1 = DebugVector(vec=Vector3.one * 2,pos=Vector3.i * 2)
dvec2 = DebugVector(vec=Vector3.i * 2,pos=Vector3.i * 2)
dvec3 = DebugVector(vec=Vector3.j * 2,pos=Vector3.i * 4)
dvec4 = DebugVector(vec=Vector3.k * 2,pos=Vector3.i * 4 + Vector3.j * 2)

[scenerot_transform.addChild(x) for x in [cube, dvec1, dvec2, dvec3, dvec4]]

xvec = DebugVector(vec=Vector3.i * 0.5, color=(1,0,0,1))
yvec = DebugVector(vec=Vector3.j * 0.5, color=(0,1,0,1))
zvec = DebugVector(vec=Vector3.k * 0.5, color=(0,0,1,1))

[axesrot_transform.addChild(x) for x in [xvec, yvec, zvec]]

print scenerot_transform.children

def step_simulation():
    

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
