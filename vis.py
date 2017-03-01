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

sensor_positions = (#[Vector3.random().unit() for x in range(10)] 
        [Vector3(1, 0, 0).rotate(Quaternion.fromAxisAngle(Vector3(0,0,1), 2*pi/3)),
         Vector3(1, 0, 0).rotate(Quaternion.fromAxisAngle(Vector3(0,0,1), 4*pi/3)),
         Vector3(1, 0, 0),
         Vector3(sqrt(2)/2, 0, sqrt(2)/2).rotate(Quaternion.fromAxisAngle(Vector3(0,0,1), 2*pi/3)),
         Vector3(sqrt(2)/2, 0, sqrt(2)/2).rotate(Quaternion.fromAxisAngle(Vector3(0,0,1), 4*pi/3)),
         Vector3(sqrt(2)/2, 0, sqrt(2)/2),
         Vector3(0, 0, 1)])

lighthouse = Lighthouse()
target_device = Device(sensorpos = sensor_positions, color = (0, 1, 0.5, 1))
slave_device = Device(sensorpos = sensor_positions, color = (1, 0.5, 0, 1))

scenerot_transform.addChild(lighthouse)
scenerot_transform.addChild(target_device)
scenerot_transform.addChild(slave_device)

pos_delta = Vector3.zero

SS_CAST_RAYS = 0
SS_COMPUTE_POS_DELTA = 1
SS_APPLY_POS_DELTA = 2
SS_COMPUTE_ROT_DELTA = 3
SS_APPLY_ROT_DELTA = 4

slave_error_bound = 1.0
slave_error = 1e20

slave_state = 0

slave_planes = []

slave_pos_delta = Vector3.zero
slave_rot_delta = Quaternion.l

slave_device_pos_tween = tween.LinearTween(Vector3.zero, Vector3.zero, speed=10.0)
slave_device_rot_tween = tween.LinearTween(Quaternion.l, Quaternion.l, speed=10.0)

target_index = 0

run_auto = False

face_sums = []

scan_dir = Lighthouse.PASS_VERTICAL

def toggle_auto():
    global run_auto
    run_auto = not run_auto

def toggle_scan_dir():
    global scan_dir
    global slave_planes

    if (scan_dir == Lighthouse.PASS_VERTICAL):
        scan_dir = Lighthouse.PASS_HORIZONTAL
    else:
        scan_dir = Lighthouse.PASS_VERTICAL

    scene_vectormanager.clear(1)

    slave_planes = lighthouse.getPlanes(target_device, scan_dir)
    for plane in slave_planes:
        scene_vectormanager.addPlane(plane, color = (1, 1, 0, 1), group = 1)

def update_slave_sensor():
    global slave_state
    global slave_planes
    global slave_pos_delta
    global slave_rot_delta
    global slave_device_pos_tween
    global slave_device_rot_tween
    global target_index
    global slave_error
    global face_sums

    slave_device.pos = slave_device_pos_tween.finish()
    slave_device.rot = slave_device_rot_tween.finish()

    _slave_planes = lighthouse.getPlanes(slave_device, scan_dir)
    scene_vectormanager.clear(4)
    for plane in _slave_planes:
        scene_vectormanager.addPlane(plane, color = (1, 0.5, 0.5, 1), group = 4)

    if slave_state == SS_CAST_RAYS:

        slave_planes = lighthouse.getPlanes(target_device, scan_dir)
        for plane in slave_planes:
            scene_vectormanager.addPlane(plane, color = (1, 1, 0, 1), group = 1)
        slave_state = SS_COMPUTE_POS_DELTA

    elif slave_state == SS_COMPUTE_POS_DELTA:

        translation_rays = []
        face_sums = []

        for plane,sp,rsp in zip(slave_planes, slave_device.getWorldSensorPos(), [sp.rotate(slave_device.rot) for sp in slave_device.sensorpos]):
            np = plane.nearest(sp)
            if np:
                translation_ray = Ray(sp, np - sp)
                translation_rays.append(translation_ray)
                scene_vectormanager.addRay(translation_ray, color = (1, 0, 0, 1), group = 2)
                face_sums.append(math.copysign(1.0, (np - sp).dot(rsp)))

        average_vec = Vector3.average([tr.vec for tr in translation_rays])

        #if(face_sum < 0):
        #    average_vec *= abs(face_sum)

        scene_vectormanager.addVector(slave_device.pos, average_vec, color = (1, 1, 1, 1), group = 2)

        slave_pos_delta = average_vec
        slave_state = SS_APPLY_POS_DELTA

    elif slave_state == SS_APPLY_POS_DELTA:

        scene_vectormanager.clear(2)
        slave_device_pos_tween.__init__(slave_device.pos, slave_device.pos + slave_pos_delta, 10.0)
        #slave_device.pos += slave_pos_delta
        slave_state = SS_COMPUTE_ROT_DELTA

    elif slave_state == SS_COMPUTE_ROT_DELTA:

        rotation_rays = []
        rotation_quats = []

        options = zip(slave_planes, slave_device.getWorldSensorPos(), [sp.rotate(slave_device.rot) for sp in slave_device.sensorpos])
        for plane,sp,rsp in options:
        #ray,sp,rsp = options[target_index % len(options)]
        #target_index += 1
            np = plane.nearest(sp)
            if np:
                rotation_ray = Ray(sp, np - sp)
                rnp = np - slave_device.pos
                rotation_rays.append(rotation_ray)
                scene_vectormanager.addRay(rotation_ray, color = (0, 1, 0, 1), group = 3)

                rotation_quats.append(Quaternion.rotationBetween(rsp, rnp))

        average_rot = Quaternion.average(rotation_quats)
        average_rotation = average_rot #Quaternion.l.slerp(average_rot, 0.95)

        scene_vectormanager.addVector(slave_device.pos, average_rotation.toAxisAngle()[0], color = (1, 1, 1, 1), group = 3)

        slave_rot_delta = average_rotation
        slave_state = SS_APPLY_ROT_DELTA

    elif slave_state == SS_APPLY_ROT_DELTA:

        scene_vectormanager.clear(3)
        slave_device_rot_tween.__init__(slave_device.rot, slave_rot_delta * slave_device.rot, 10.0)
        #slave_device.rot = slave_rot_delta * slave_device.rot
        slave_state = SS_COMPUTE_POS_DELTA

def move_target_sensor():
    global pos_delta
    global slave_state
    scene_vectormanager.clear(0)
    target_device.pos += pos_delta
    pos_delta = Vector3.random().unit() * 2
    scene_vectormanager.addVector(target_device.pos, pos_delta, (1, 1, 0, 1), group = 0)
    slave_state = SS_CAST_RAYS

def rotate_target_sensor():
    global slave_state
    target_device.rot = Quaternion.fromAxisAngle(Vector3.random(), pi * 2 * (random.random() / 10) - pi) * target_device.rot
    scene_vectormanager.clear(0)
    slave_state = SS_CAST_RAYS

def sync_states():
    global slave_state
    #slave_device.pos = target_device.pos
    #slave_device.rot = target_device.rot

    slave_device_pos_tween.snap(target_device.pos)
    slave_device_rot_tween.snap(target_device.rot)

def move_out():
    slave_device_pos_tween.snap(slave_device.pos + (slave_device.pos - lighthouse.pos).unit() * 0.5)

def move_in():
    slave_device_pos_tween.snap(slave_device.pos - (slave_device.pos - lighthouse.pos).unit() * 0.5)

## This function updates the simulation state
def step_simulation():
    global pos_delta
    scene_vectormanager.clear()
    #cube.pos += pos_delta
    #pos_delta = Vector3.random().unit() * 5
    #scene_vectormanager.addVector(cube.pos, pos_delta, (1, 1, 0, 1))

GRID_SIZE = 2

print_timer = tween.PeriodicTimer(10)

def loop_simulation(dt):
    global slave_error

    if(run_auto):
        if(slave_device_pos_tween.done() and slave_device_rot_tween.done()):
            scene_vectormanager.clear()
            update_slave_sensor()

    slave_device.pos = slave_device_pos_tween.step(dt)
    slave_device.rot = slave_device_rot_tween.step(dt)

    if print_timer.tick():
        scene_vectormanager.clear(10)
        target_rays = lighthouse.getRays(target_device)
        delta_vecs = []
        for ray,sp in zip(target_rays, [slave_device.pos + rsp.rotate(slave_device.rot) for rsp in slave_device.sensorpos]):
            np = ray.nearest(sp)
            if np:
                delta_vecs.append(np - sp)
                scene_vectormanager.addRay(Ray(sp, np - sp), color=(1,1,1,1), group=10)
        
        slave_error = sum([vec.magnitude() for vec in delta_vecs])
        print "E:", slave_error, "FS:", face_sums
    #scene_vectormanager.clear()
    #r = range(1-GRID_SIZE, GRID_SIZE)
    #for i in r:
    #    for j in r:
    #        for k in r:
    #            pos = Vector3(i,j,k)
    #            direc = (pos.unit() * 0.5 * sin(t * 2 + pos.magnitude())) if (pos.magnitude() != 0) else Vector3.zero
    #            direc = direc.rotate(Quaternion.fromAxisAngle(Vector3.j, pi/4))
    #            scene_vectormanager.addVector(pos, direc, (1,1,0,1)) #((i + GRID_SIZE - 1)/float(GRID_SIZE * 2),(j + GRID_SIZE - 1)/float(GRID_SIZE * 2),(k + GRID_SIZE - 1)/float(GRID_SIZE * 2),1))
    #            scene_vectormanager.addPlane(Plane(pos, direc))

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
    if(symbol == key.M):
        move_target_sensor()
    if(symbol == key.R):
        rotate_target_sensor()
    if(symbol == key.N):
        update_slave_sensor()
    if(symbol == key.C):
        sync_states()
    if(symbol == key.O):
        move_out()
    if(symbol == key.I):
        move_in()

    if(symbol == key.A):
        toggle_auto()

    if(symbol == key.S):
        toggle_scan_dir()

def process_loop(dt):
    global t
    t += dt

    loop_simulation(dt)
    pass

pyglet.clock.schedule(process_loop)
pyglet.app.run()
