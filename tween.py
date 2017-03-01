import vector

class LinearTween(object):
    def __init__(self, a, b, speed):
        self.a = a
        self.b = b
        self.t = 0.0
        self.speed = speed

    def step(self, dt):
        if self.t < 1.0:
            self.t += (dt * self.speed)
            if self.t > 1.0:
                self.t = 1.0
            return self.a.lerp(self.b, self.t) if type(self.a) == vector.Vector3 else self.a.slerp(self.b, self.t)
        else:
            return self.b

    def done(self):
        return self.t == 1.0

    def finish(self):
        self.t = 1.0
        return self.b

    def snap(self, c):
        self.a = self.b = c
        self.t = 1.0

class PeriodicTimer(object):
    def __init__(self, period):
        self.count = 0
        self.period = period

    def tick(self):
        self.count += 1
        if self.count >= self.period:
            self.count = 0
            return True
        return False
