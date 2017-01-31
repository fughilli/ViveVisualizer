import math
import random

class Vector3Meta(type):
    def __getattr__(self, name):
        if (name == 'zero'):
            return Vector3(0.0,0.0,0.0)
        if (name == 'one'):
            return Vector3(1.0,1.0,1.0)
        if (name == 'i'):
            return Vector3(1.0,0.0,0.0)
        if (name == 'j'):
            return Vector3(0.0,1.0,0.0)
        if (name == 'k'):
            return Vector3(0.0,0.0,1.0)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if (name in ['zero', 'one', 'i', 'j', 'k']):
            print "Something attempted to set %s to %s" % (name, value)

class Vector3(object):
    __metaclass__ = Vector3Meta

    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def rotate(self, quat):
        vec_q = Quaternion(self.x, self.y, self.z, 0)
        vec_q = (quat * vec_q) * quat.conjugate()
        return Vector3(vec_q.x, vec_q.y, vec_q.z)

    @staticmethod
    def random():
        return Vector3(random.random() - 0.5, random.random() - 0.5,
                       random.random() - 0.5) * 2

    def __div__(self, other):
        if not (type(other) == float or type(other) == int):
            raise Exception("Vector3 / %s not supported" % type(other))
        return Vector3(self.x / other, self.y / other, self.z / other)

    def __mul__(self, other):
        if not (type(other) == float or type(other) == int):
            raise Exception("Vector3 * %s not supported" % type(other))
        ret = Vector3(self.x * other, self.y * other, self.z * other)
        return ret

    def __add__(self, other):
        if not type(other) == Vector3:
            raise Exception("Vector3 + %s not supported" % type(other))
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __neg__(self):
        return Vector3(-self.x, -self.y, -self.z)

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def rotationAroundAxis(self, angle):
        axis = self.unit() * math.sin(angle / 2.0)
        return Quaternion(axis.x, axis.y, axis.z, math.cos(angle / 2.0))

    def cross(self, other):
        return Vector3(
        self.y * other.z - self.z * other.y,
        self.z * other.x - self.x * other.z,
        self.x * other.y - self.y * other.x)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def project(self, other):
        udir = other.unit()
        return self.dot(udir) * udir

    def orthogonal(self, other):
        return self - self.project(other)

    def unit(self):
        return self / self.magnitude()

    def __getitem__(self, index):
        return [self.x,self.y,self.z][index]

    def __repr__(self):
        return "Vector3(<%f,%f,%f>)" % (self.x, self.y, self.z)

class QuaternionMeta(type):
    def __getattr__(self, name):
        if (name == 'zero'):
            return Quaternion(0.0,0.0,0.0,0.0)
        if (name == 'one'):
            return Quaternion(1.0,1.0,1.0,1.0)
        if (name == 'i'):
            return Quaternion(1.0,0.0,0.0,0.0)
        if (name == 'j'):
            return Quaternion(0.0,1.0,0.0,0.0)
        if (name == 'k'):
            return Quaternion(0.0,0.0,1.0,0.0)
        if (name == 'l'):
            return Quaternion(0.0,0.0,0.0,1.0)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if (name in ['zero', 'one', 'i', 'j', 'k', 'l']):
            print "Something attempted to set %s to %s" % (name, value)

class Quaternion(object):
    __metaclass__ = QuaternionMeta

    def __init__(self, x, y, z, w):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)

    def toAxisAngle(self):
        quat = self
        if self.w > 1:
            quat = self.unit()
        angle = math.acos(self.w) * 2
        s = math.sqrt(1 - self.w**2)
        axis = Vector3.i
        if (s < 0.001):
            axis.x = self.x
            axis.y = self.y
            axis.z = self.z
        else:
            axis.x = self.x / s
            axis.y = self.y / s
            axis.z = self.z / s
        #axis = Vector3.i
        #if angle != 0:
        #    axis = Vector3(self.x, self.y, self.z) / sin(angle / 2)
        return axis,angle

    @staticmethod
    def fromAxisAngle(axis, angle):
        return axis.rotationAroundAxis(angle)

    @staticmethod
    def rotationBetween(va, vb):
        if(va.magnitude() == 0 or vb.magnitude() == 0):
            return Quaternion.l

        va = va.unit()
        vb = vb.unit()

        if ((va + vb).magnitude() == 0):
            return Quaternion(*va.cross(vb), w=0)

        vh = (va + vb).unit()
        return Quaternion(*va.cross(vh), w=va.dot(vh))

    def norm(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2 + self.w ** 2)

    def unit(self):
        return self / self.norm()

    def conjugate(self):
        return Quaternion(-self.x, -self.y, -self.z, self.w)

    def __div__(self, other):
        if type(other) == float or type(other) == int:
            return Quaternion(self.x / other, self.y / other, self.z / other,
                              self.w / other)
        raise Exception("Quaternion / %s not supported" % type(other))

    def __mul__(self, other):
        if type(other) == Quaternion:
            return Quaternion(
            self.w*other.x + self.x*other.w + self.y*other.z - self.z*other.y,
            self.w*other.y - self.x*other.z + self.y*other.w + self.z*other.x,
            self.w*other.z + self.x*other.y - self.y*other.x + self.z*other.w,
            self.w*other.w - self.x*other.x - self.y*other.y - self.z*other.z)
        if type(other) == float or type(other) == int:
            return Quaternion(self.x * other, self.y * other, self.z * other,
                              self.w * other)
        raise Exception("Quaternion * %s not supported" % type(other))

    def __sub__(self, other):
        if not type(other) == Quaternion:
            raise Exception("Quaternion - %s not supported" % type(other))
        return Quaternion(self.x - other.x,
                          self.y - other.y,
                          self.z - other.z,
                          self.w - other.w)

    def __add__(self, other):
        if not type(other) == Quaternion:
            raise Exception("Quaternion + %s not supported" % type(other))
        return Quaternion(self.x + other.x,
                          self.y + other.y,
                          self.z + other.z,
                          self.w + other.w)

    def __neg__(self):
        return Quaternion(-self.x, -self.y, -self.z, -self.w)

    def __getitem__(self, index):
        return [self.x,self.y,self.z,self.w][index]

    def __repr__(self):
        return "Quaternion(<%f,%f,%f,%f>)" % (self.x, self.y, self.z, self.w)

class Ray(object):
    def __init__(self, origin, vec):
        self.origin = origin
        self.vec = vec

    def nearest(self, point):
        relative = point - self.origin
        if relative.dot(self.vec) < 0:
            return None

        return self.origin + relative.project(self.vec)

class Plane(object):
    def __init__(self, origin, normal):
        self.origin = origin
        self.normal = normal

    def nearest(self, point):
        relative = point - self.origin
        return self.origin + relative.orthogonal(self.vec)
