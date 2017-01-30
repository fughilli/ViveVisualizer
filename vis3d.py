import math
import objimporter
import pyglet
import pyglet.gl
import vector

class Transform(object):
    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l, parent=None, shadow=None):
        self.shadow = shadow
        self.parent = parent
        self.children = []
        self.pos = pos
        self.rot = rot

    #def getPos(self):
    #    return (self.parent.getPos() + self.pos.rotate(self.parent.getRot())) if self.parent else (self.pos)

    #def getRot(self):
    #    return (self.parent.getRot() * self.rot) if self.parent else (self.rot)

    def addChild(self, child=None):
        print "addChild %s %s" % (self, child)
        if child:
            child.parent = self
            self.children.append(child)
        else:
            ret = type(self)()
            self.children.append(ret)
            return ret

class GLDrawTransform(Transform):
    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l, parent=None, shadow=None):
        super(GLDrawTransform, self).__init__(pos, rot, parent, shadow)

    def draw(self):
        #print "GLDrawTransform.draw %s (%s, %s)" % (self, self.rot, self.pos)
        pyglet.gl.glPushMatrix()

        axis,angle = self.shadow.rot.toAxisAngle() if self.shadow else self.rot.toAxisAngle()
        pyglet.gl.glTranslatef(*(self.shadow.pos if self.shadow else self.pos))
        pyglet.gl.glRotatef(angle / math.pi * 180, *axis)

        for child in self.children:
            child.draw()

        pyglet.gl.glPopMatrix()

class OBJObject(GLDrawTransform):
    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l, parent = None):
        super(OBJObject, self).__init__(pos, rot, parent)
        self.vertices = []
        self.indices = []

    def imp(self, filename):
        self.vertices,self.indices = objimporter.OBJImporter.imp(filename, flat=True)

    def draw(self):
        #print "OBJObject.draw %s (%s, %s)" % (self, self.rot, self.pos)
        pyglet.gl.glPushMatrix()

        axis,angle = self.rot.toAxisAngle()
        pyglet.gl.glTranslatef(*self.pos)
        pyglet.gl.glRotatef(angle / math.pi * 180, *axis)

        pyglet.gl.glColor4f(1.0,0,0,1.0)

        pyglet.graphics.draw_indexed(len(self.vertices)/3, pyglet.gl.GL_TRIANGLES, self.indices, ('v3f', self.vertices))

        pyglet.gl.glPopMatrix()

        pass

class DebugVector(GLDrawTransform):
    def __init__(self, vec, color=(0, 1, 0, 1), pos=vector.Vector3.zero, rot=vector.Quaternion.l, parent = None):
        super(DebugVector, self).__init__(pos, rot, parent)
        self.vec = vec
        self.color = color

    def draw(self):
        #print "DebugVector.draw %s (%s, %s)" % (self, self.rot, self.pos)
        pyglet.gl.glPushMatrix()
        temprot = vector.Quaternion.rotationBetween(vector.Vector3.i, self.vec)
        axis,angle = temprot.toAxisAngle()
        pyglet.gl.glTranslatef(*self.pos)
        pyglet.gl.glRotatef(angle / math.pi * 180, *axis)

        pyglet.gl.glColor4f(*self.color)

        mag = self.vec.magnitude()

        pyglet.graphics.draw_indexed(5, pyglet.gl.GL_LINES, [0,1,1,2,1,3,1,4,2,3,3,4,4,2],
                ('v3f', [0,0,0,
                         mag,0,0,
                         mag - 0.1,0.1,-0.05,
                         mag - 0.1,-0.1,-0.05,
                         mag - 0.1,0,0.1]))

        pyglet.gl.glPopMatrix()
