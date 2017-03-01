import vis3d
import vector

class Lighthouse(vis3d.OBJObject):
    PASS_VERTICAL = 1
    PASS_HORIZONTAL = 2

    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l, parent = None):
        super(Lighthouse, self).__init__(pos, rot, parent)

        self.imp("lighthouse.obj")

    def getRay(self, sensorpos):
        return vector.Ray(self.pos, sensorpos - self.pos)

    def getPlane(self, sensorpos, p=PASS_VERTICAL):
        if p == self.PASS_VERTICAL:
            return vector.Plane(self.pos, vector.Vector3.j.cross(sensorpos - self.pos))
        if p == self.PASS_HORIZONTAL:
            return vector.Plane(self.pos, vector.Vector3.k.cross(sensorpos - self.pos))

    def getRays(self, device):
        return [self.getRay(sp) for sp in device.getWorldSensorPos()]

    def getPlanes(self, device, p=PASS_VERTICAL):
        return [self.getPlane(sp, p) for sp in device.getWorldSensorPos()]

class Device(vis3d.DebugVectorManager):
    def __init__(self, pos = vector.Vector3.zero, rot = vector.Quaternion.l, sensorpos=[], color = (0, 1, 1, 1), parent = None):
        super(Device, self).__init__(pos, rot, parent)

        self.sensorpos = sensorpos

        for sp in sensorpos:
            self.addVector(pos = vector.Vector3.zero, vec = sp, color = color)

    def getWorldSensorPos(self):
        return [self.pos + sp.rotate(self.rot) for sp in self.sensorpos]
