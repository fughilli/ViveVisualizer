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

    def __sub__(self, other):
        if not type(other) == Vector3:
            raise Exception("Vector3 - %s not supported" % type(other))
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

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
        return udir * self.dot(udir)

    def orthogonal(self, other):
        return self - self.project(other)

    def unit(self):
        return self / self.magnitude()

    def lerp(self, other, t):
        return (self * (1 - t)) + (other * t)

    def rotateAxisAngle(self, axis, angle):
        return self.rotate(Quaternion.fromAxisAngle(axis, angle))

    @staticmethod
    def average(vectors):
        if vectors:
            return reduce(lambda a,b : a+b, vectors, Vector3.zero) / len(vectors)
        else:
            return Vector3.zero

    @staticmethod
    def enclosingAABB(vectors):
        if len(vectors) == 0:
            return (Vector3.zero, Vector3.zero)
        return (
                reduce(lambda a,b : Vector3(min((a.x,b.x)), min((a.y,b.y)), min((a.z,b.z))), vectors),
                reduce(lambda a,b : Vector3(max((a.x,b.x)), max((a.y,b.y)), max((a.z,b.z))), vectors)
               )

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

    @staticmethod
    def random():
        return Quaternion(*[random.random() - 0.5 for i in range(4)]).unit()

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

    @staticmethod
    def average(quats):
        if quats:
            return (reduce(lambda a,b : a+b, quats) / len(quats)).unit()
        else:
            return Quaternion.l

    def dot(self, other):
        return math.sqrt(self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w)

    def slerp(self, endpt, t):
        qret = self * 1.0
        cosHalfTheta = self.dot(endpt)

        if(abs(cosHalfTheta) >= 1.0):
            return qret

        halfTheta = math.acos(cosHalfTheta)
        sinHalfTheta = math.sqrt(1.0 - cosHalfTheta ** 2)

        if(abs(sinHalfTheta) < 0.001):
            qret.x = (self.x*0.5 + endpt.x*0.5)
            qret.y = (self.y*0.5 + endpt.y*0.5)
            qret.z = (self.z*0.5 + endpt.z*0.5)
            qret.w = (self.w*0.5 + endpt.w*0.5)
            return qret

        ratA = math.sin((1.0 - t) * halfTheta) / sinHalfTheta
        ratB = math.sin(t * halfTheta) / sinHalfTheta

        qret.x = (self.x*ratA + endpt.x*ratB)
        qret.y = (self.y*ratA + endpt.y*ratB)
        qret.z = (self.z*ratA + endpt.z*ratB)
        qret.w = (self.w*ratA + endpt.w*ratB)

        return qret

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

    @staticmethod
    def average(rays):
        average_pos = Vector3.average([ray.origin for ray in rays])
        average_vec = Vector3.average([ray.vec for ray in rays])

        return Ray(average_pos, average_vec)

    @staticmethod
    def fromPitchYaw(pitch,yaw):
        target = Vector3.i.rotateAxisAngle(Vector3.j,pitch).rotateAxisAngle(Vector3.k,yaw) * 10

        return Ray(Vector3.zero, target)

class Plane(object):
    def __init__(self, origin, normal):
        self.origin = origin
        self.normal = normal

    def nearest(self, point):
        relative = point - self.origin
        return self.origin + relative.orthogonal(self.normal)

def __helper_dot(a, b):
    return sum(lambda x,y : x*y, zip(a,b))

class Matrix4x4Meta(type):
    def __getattr__(self, name):
        if (name == 'zero'):
            return Matrix4x4(*([0.0] * 16))
        if (name == 'one'):
            return Matrix4x4(*([1.0] * 16))
        if (name == 'identity'):
            return Matrix4x4(1.0, 0.0, 0.0, 0.0,
                             0.0, 1.0, 0.0, 0.0,
                             0.0, 0.0, 1.0, 0.0,
                             0.0, 0.0, 0.0, 1.0)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if (name in ['zero', 'one', 'i', 'j', 'k', 'l']):
            print "Something attempted to set %s to %s" % (name, value)

class Matrix4x4(object):
    __metaclass__ = Matrix4x4Meta

    def __init__(self, *components):
        self.components = [float(x) for x in components]

    def row(self, idx):
        return self.components[idx * 4 : (idx + 1) * 4]

    def col(self, idx):
        return self.components[idx::4]

    def __mul__(self, other):
        if type(other) == Vector3:
            ext_v = [other.x, other.y, other.z, 1.0]
            return Vector3([__helper_dot(self.row(i), ext_v) for i in range(3)])

    def component(self, r, c):
        return self.components[r*4 + c]

    def rotation(self):
        tr = self.component(0,0) + self.component(1,1) + self.component(2,2)
        q = Quaternion.zero

        if (tr > 0):
            S = math.sqrt(tr+1.0) * 2
            q.w = 0.25 * S
            q.x = (self.component(2,1) - self.component(1,2)) / S
            q.y = (self.component(0,2) - self.component(2,0)) / S
            q.z = (self.component(1,0) - self.component(0,1)) / S
        elif ((self.component(0,0) > self.component(1,1)) and
              (self.component(0,0) > self.component(2,2))):
            S = math.sqrt(1.0 + self.component(0,0) - self.component(1,1) -
                          self.component(2,2)) * 2
            q.w = (self.component(2,1) - self.component(1,2)) / S
            q.x = 0.25 * S
            q.y = (self.component(0,1) + self.component(1,0)) / S
            q.z = (self.component(0,2) + self.component(2,0)) / S
        elif (self.component(1,1) > self.component(2,2)):
            S = math.sqrt(1.0 + self.component(1,1) - self.component(0,0) -
                          self.component(2,2)) * 2
            q.w = (self.component(0,2) - self.component(2,0)) / S
            q.x = (self.component(0,1) + self.component(1,0)) / S
            q.y = 0.25 * S
            q.z = (self.component(1,2) + self.component(2,1)) / S
        else:
            S = math.sqrt(1.0 + self.component(2,2) - self.component(0,0) -
                          self.component(1,1)) * 2
            q.w = (self.component(1,0) - self.component(0,1)) / S
            q.x = (self.component(0,2) + self.component(2,0)) / S
            q.y = (self.component(1,2) + self.component(2,1)) / S
            q.z = 0.25 * S

        return q
