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

class DebugVector(GLDrawTransform):
    def __init__(self, vec, color=(0, 1, 0, 1), pos=vector.Vector3.zero,
                 rot=vector.Quaternion.l, parent = None):
        super(DebugVector, self).__init__(pos, rot, parent)
        self.vec = vec
        self.color = color

    def draw(self):

        pyglet.gl.glPushMatrix()
        temprot = vector.Quaternion.rotationBetween(vector.Vector3.i, self.vec)
        axis,angle = temprot.toAxisAngle()
        pyglet.gl.glTranslatef(*self.pos)
        pyglet.gl.glRotatef(angle / math.pi * 180, *axis)

        pyglet.gl.glColor4f(*self.color)

        mag = self.vec.magnitude()

        pyglet.graphics.draw_indexed(5, pyglet.gl.GL_LINES,
                                     [0,1,1,2,1,3,1,4,2,3,3,4,4,2],
                                     ('v3f', [0,0,0,
                                              mag,0,0,
                                              mag - 0.1,0.1,-0.05,
                                              mag - 0.1,-0.1,-0.05,
                                              mag - 0.1,0,0.1]))

        pyglet.gl.glPopMatrix()
