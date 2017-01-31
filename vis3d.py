import math
import objimporter
import pyglet
import pyglet.gl
import vector

class Transform(object):
    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l,
                 parent=None, shadow=None):
        self.shadow = shadow
        self.parent = parent
        self.children = []
        self.pos = pos
        self.rot = rot

    def addChild(self, child=None):
        if child:
            child.parent = self
            self.children.append(child)
        else:
            ret = type(self)()
            self.children.append(ret)
            return ret

class GLDrawTransform(Transform):
    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l,
                 parent=None, shadow=None):
        super(GLDrawTransform, self).__init__(pos, rot, parent, shadow)

    def draw(self):

        pyglet.gl.glPushMatrix()

        axis,angle = (self.shadow.rot.toAxisAngle() if self.shadow else
                      self.rot.toAxisAngle())
        pyglet.gl.glTranslatef(*(self.shadow.pos if self.shadow else self.pos))
        pyglet.gl.glRotatef(angle / math.pi * 180, *axis)

        for child in self.children:
            child.draw()

        pyglet.gl.glPopMatrix()

class OBJObject(GLDrawTransform):
    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l,
                 parent = None):
        super(OBJObject, self).__init__(pos, rot, parent)
        self.vertices = []
        self.indices = []

    def imp(self, filename):
        self.vertices,self.indices = objimporter.OBJImporter.imp(filename,
                                                                 flat=True)

    def draw(self):

        pyglet.gl.glPushMatrix()

        axis,angle = self.rot.toAxisAngle()
        pyglet.gl.glTranslatef(*self.pos)
        pyglet.gl.glRotatef(angle / math.pi * 180, *axis)

        pyglet.gl.glColor4f(1.0,0,0,1.0)

        pyglet.graphics.draw_indexed(len(self.vertices)/3,
                                     pyglet.gl.GL_TRIANGLES, self.indices,
                                     ('v3f', self.vertices))

        pyglet.gl.glPopMatrix()

        pass

class DebugVectorManager(GLDrawTransform):
    def __init__(self, pos=vector.Vector3.zero, rot=vector.Quaternion.l,
                 parent = None):
        super(DebugVectorManager, self).__init__(pos, rot, parent)

    def clear(self):
        self.children = []

    def addVector(self, pos, vec, color=(1, 0, 0, 1)):
        self.addChild(DebugVector(pos=pos, vec=vec, color=color))

    def addRay(self, ray, color=(1, 0, 0, 1)):
        self.addVector(ray.origin, ray.vec, color)

    def addPlane(self, plane, color=(1, 0, 0, 0.5)):
        self.addChild(DebugPlane(pos=plane.origin, normal=plane.normal, color=color))

class DebugVector(GLDrawTransform):
    def __init__(self, vec, color=(0, 1, 0, 1), pos=vector.Vector3.zero,
                 rot=vector.Quaternion.l, parent = None):
        super(DebugVector, self).__init__(pos, rot, parent)
        self.vec = vec
        self.color = color

    def draw(self):

        pyglet.gl.glPushMatrix()
        pyglet.gl.glTranslatef(*self.pos)
        pyglet.gl.glColor4f(*self.color)

        x,y,z = self.vec

        pyglet.graphics.draw_indexed(8, pyglet.gl.GL_LINES,
                                     [0,1,2,3,4,5,6,7],
                                     ('v3f', [0,0,0,
                                              x,y,z,
                                              x+0.04,y,z,
                                              x-0.04,y,z,
                                              x,y+0.04,z,
                                              x,y-0.04,z,
                                              x,y,z+0.04,
                                              x,y,z-0.04]))

        pyglet.gl.glPopMatrix()

class DebugPlane(GLDrawTransform):
    def __init__(self, normal, color=(0, 1, 0, 0.5), pos=vector.Vector3.zero,
                 rot=vector.Quaternion.l, parent=None):
        super(DebugPlane, self).__init__(pos, rot, parent)
        self.normal = normal
        self.color = color

    def draw(self):

        pyglet.gl.glPushMatrix()

        pyglet.gl.glTranslatef(*self.pos)

        pyglet.gl.glColor4f(*self.color)

        major = 0

        if (self.normal.z != 0 or self.normal.y != 0):
            major = vector.Vector3(0, -self.normal.z, self.normal.y)
        else:
            major = vector.Vector3(-self.normal.z, 0, self.normal.x)

        minor = self.normal.cross(major)

        if(minor.magnitude() != 0):
            minor = minor.unit() * 0.2
        if(major.magnitude() != 0):
            major = major.unit() * 0.2

        Mx,My,Mz = major
        mx,my,mz = minor

        pyglet.graphics.draw_indexed(4, pyglet.gl.GL_LINES,
                                     [0,1,1,2,2,3,3,0],
                                     ('v3f', [Mx+mx,My+my,Mz+mz,
                                              Mx-mx,My-my,Mz-mz,
                                              -Mx-mx,-My-my,-Mz-mz,
                                              -Mx+mx,-My+my,-Mz+mz]))

        pyglet.gl.glPopMatrix()
