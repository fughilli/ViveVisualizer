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

sensor_positions = ([Vector3(4.8,0,0.3), Vector3(0,0,4.0),
                     Vector3(-2.1,4.1,0.3), Vector3(-2.1,-4.1,0.3)])

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

slave_rays = []

slave_pos_delta = Vector3.zero
slave_rot_delta = Quaternion.l

slave_device_pos_tween = tween.LinearTween(Vector3.zero, Vector3.zero,
                                           speed=10.0)
slave_device_rot_tween = tween.LinearTween(Quaternion.l, Quaternion.l,
                                           speed=10.0)

target_index = 0

run_auto = False

face_sums = []

scan_dir = Lighthouse.PASS_VERTICAL

view_rays = []

angle_order = True

def toggle_auto():
    global run_auto
    run_auto = not run_auto

def toggle_scan_dir():
    global scan_dir
    global slave_rays

    if (scan_dir == Lighthouse.PASS_VERTICAL):
        scan_dir = Lighthouse.PASS_HORIZONTAL
    else:
        scan_dir = Lighthouse.PASS_VERTICAL

    scene_vectormanager.clear(1)

    slave_rays = lighthouse.getRays(target_device)
    for ray in slave_rays:
        scene_vectormanager.addRay(ray, color = (1, 1, 0, 1), group = 1)

def toggle_angle_order():
    global angle_order

    angle_order = not angle_order

def update_slave_sensor():
    global slave_state
    global slave_rays
    global slave_pos_delta
    global slave_rot_delta
    global slave_device_pos_tween
    global slave_device_rot_tween
    global target_index
    global slave_error
    global face_sums

    slave_device.pos = slave_device_pos_tween.finish()
    slave_device.rot = slave_device_rot_tween.finish()

    _slave_rays = lighthouse.getRays(slave_device)
    scene_vectormanager.clear(4)
    for ray in _slave_rays:
        scene_vectormanager.addRay(ray, color = (1, 0.5, 0.5, 1), group = 4)

    if slave_state == SS_CAST_RAYS:

        slave_rays = lighthouse.getRays(target_device)
        for ray in slave_rays:
            scene_vectormanager.addRay(ray, color = (1, 1, 0, 1), group = 1)
        slave_state = SS_COMPUTE_POS_DELTA

    elif slave_state == SS_COMPUTE_POS_DELTA:

        translation_rays = []
        face_sums = []

        slave_sensorpos = slave_device.getWorldSensorPos()
        target_sensorpos = []

        for ray,sp,rsp in zip(slave_rays, slave_sensorpos,
                              [sp.rotate(slave_device.rot) for sp in
                               slave_device.sensorpos]):
            np = ray.nearest(sp)
            if np:
                target_sensorpos.append(np)
                translation_ray = Ray(sp, np - sp)
                translation_rays.append(translation_ray)
                scene_vectormanager.addRay(translation_ray,
                                           color = (1, 0, 0, 1), group = 2)
                face_sums.append(math.copysign(1.0, (np - sp).dot(rsp)))

        slave_aabb = Vector3.enclosingAABB(slave_sensorpos)
        target_aabb = Vector3.enclosingAABB(target_sensorpos)

        target_pos = Vector3.average(target_sensorpos)
        lighthouse_vector = target_pos - lighthouse.pos

        target_aabb_size = (target_aabb[0] - target_aabb[1]).magnitude()
        if (target_aabb_size > 0):
            lighthouse_vector = (lighthouse_vector *
                                 ((slave_aabb[0] - slave_aabb[1]).magnitude() /
                                  target_aabb_size - 1.0))
        else:
            lighthouse_vector = Vector3.zero

        average_vec = Vector3.average([tr.vec for tr in translation_rays])

        #if(face_sum < 0):
        #    average_vec *= abs(face_sum)

        scene_vectormanager.addVector(slave_device.pos, average_vec,
                                      color = (1, 1, 1, 1), group = 2)
        scene_vectormanager.addVector(slave_device.pos + average_vec,
                                      lighthouse_vector, color = (1, 1, 1, 1),
                                      group = 2)

        slave_pos_delta = average_vec + lighthouse_vector
        slave_state = SS_APPLY_POS_DELTA

    elif slave_state == SS_APPLY_POS_DELTA:

        scene_vectormanager.clear(2)
        slave_device_pos_tween.__init__(slave_device.pos, slave_device.pos +
                                        slave_pos_delta, 10.0)
        slave_state = SS_COMPUTE_ROT_DELTA

    elif slave_state == SS_COMPUTE_ROT_DELTA:

        rotation_rays = []
        rotation_quats = []

        options = zip(slave_rays, slave_device.getWorldSensorPos(),
                      [sp.rotate(slave_device.rot) for sp in
                       slave_device.sensorpos])
        for ray,sp,rsp in options:
            np = ray.nearest(sp)
            if np:
                rotation_ray = Ray(sp, np - sp)
                rnp = np - slave_device.pos
                rotation_rays.append(rotation_ray)
                scene_vectormanager.addRay(rotation_ray, color = (0, 1, 0, 1),
                                           group = 3)

                rotation_quats.append(Quaternion.rotationBetween(rsp, rnp))

        average_rot = Quaternion.average(rotation_quats)
        average_rotation = average_rot

        scene_vectormanager.addVector(slave_device.pos,
                                      average_rotation.toAxisAngle()[0],
                                      color = (1, 1, 1, 1), group = 3)

        slave_rot_delta = average_rotation
        slave_state = SS_APPLY_ROT_DELTA

    elif slave_state == SS_APPLY_ROT_DELTA:

        scene_vectormanager.clear(3)
        slave_device_rot_tween.__init__(slave_device.rot,
                                        slave_rot_delta * slave_device.rot,
                                        10.0)
        slave_state = SS_COMPUTE_POS_DELTA

def move_target_sensor():
    global pos_delta
    global slave_state
    scene_vectormanager.clear(0)
    target_device.pos += pos_delta
    pos_delta = Vector3.random().unit() * 2
    scene_vectormanager.addVector(target_device.pos, pos_delta, (1, 1, 0, 1),
                                  group = 0)
    slave_state = SS_CAST_RAYS

def rotate_target_sensor():
    global slave_state
    target_device.rot = (Quaternion.fromAxisAngle(Vector3.random(), pi * 2 *
                                                  (random.random() / 10) - pi) *
                                                 target_device.rot)
    scene_vectormanager.clear(0)
    slave_state = SS_CAST_RAYS

def sync_states():
    global slave_state

    slave_device_pos_tween.snap(target_device.pos)
    slave_device_rot_tween.snap(target_device.rot)

def move_out():
    slave_device_pos_tween.snap(slave_device.pos + (slave_device.pos -
                                                    lighthouse.pos).unit() *
                                                   0.5)

def move_in():
    slave_device_pos_tween.snap(slave_device.pos - (slave_device.pos -
                                                    lighthouse.pos).unit() *
                                                   0.5)

## This function updates the simulation state
def step_simulation():
    global pos_delta
    scene_vectormanager.clear()

print_timer = tween.PeriodicTimer(10)

def loop_simulation(dt):
    global slave_error

    if(run_auto):
        if(slave_device_pos_tween.done() and slave_device_rot_tween.done()):
            scene_vectormanager.clear()
            update_slave_sensor()

    slave_device.pos = slave_device_pos_tween.step(dt * 10)
    slave_device.rot = slave_device_rot_tween.step(dt * 10)

    scene_vectormanager.clear(15)
    for r in view_rays:
        scene_vectormanager.addRay(r, color=(0,0,1,1), group=15)

    if print_timer.tick():
        scene_vectormanager.clear(10)
        target_rays = lighthouse.getRays(target_device)
        delta_vecs = []
        for ray,sp in zip(target_rays, [slave_device.pos +
                                        rsp.rotate(slave_device.rot) for rsp in
                                        slave_device.sensorpos]):
            np = ray.nearest(sp)
            if np:
                delta_vecs.append(np - sp)
                scene_vectormanager.addRay(Ray(sp, np - sp), color=(1,1,1,1),
                                           group=10)

        slave_error = sum([vec.magnitude() for vec in delta_vecs])
        print "E:", slave_error, "FS:", face_sums

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

mouse_move_target = False

@win.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if (buttons & pyglet.window.mouse.LEFT and not
        buttons & pyglet.window.mouse.RIGHT):
        delta_rot = (Quaternion.fromAxisAngle(Vector3.j,
                                              float(dx) / win.width * 2 * pi) *
                     Quaternion.fromAxisAngle(Vector3.i,
                                              -float(dy) / win.height * 2 * pi))
        if mouse_move_target:
            target_device.rot = (scenerot_transform.rot.conjugate() *
                                delta_rot * (scenerot_transform.rot *
                                             target_device.rot)).unit()
        else:
            scenerot_transform.rot = (delta_rot * scenerot_transform.rot).unit()
    elif (buttons & pyglet.window.mouse.RIGHT and not
          buttons & pyglet.window.mouse.LEFT):
        delta_pos = Vector3(dx,dy,0) * 0.05
        if mouse_move_target:
            target_device.pos += delta_pos.rotate(
                scenerot_transform.rot.conjugate())
        else:
            camera_offset_transform.pos += delta_pos

@win.event
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    camera_offset_transform.pos += Vector3(0,0,scroll_y) * 0.5

@win.event
def on_key_press(symbol, modifiers):
    global mouse_move_target

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

    if(symbol == key.K):
        toggle_angle_order()

    if(symbol == key.D):
        mouse_move_target = True

@win.event
def on_key_release(symbol, modifiers):
    global mouse_move_target

    if(symbol == key.D):
        mouse_move_target = False

def process_loop(dt):
    global t
    t += dt

    loop_simulation(dt)
    pass

pyglet.clock.schedule(process_loop)
pyglet.app.run()
