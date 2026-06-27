from . import integrator
import numpy as np
import pinocchio as pin
import time, threading

class Simulator:
    def __init__(self, model, policy, dt, q0=None, v0=None):
        self.model = model
        self.data = model.createData()
        self.policy = policy
        self.dt = dt
        self.q = (q0 if q0 is not None else pin.neutral(model)).copy()
        self.v = (v0 if v0 is not None else np.zeros(model.nv)).copy()
        self.t = 0.0
        self._stop = threading.Event()

    def tick(self):
        tau = self.policy(self.model, self.data, self.q, self.v)
        self.q, self.v = integrator.step(self.model, self.data, self.q, self.v, tau, self.dt)
        self.t += self.dt

    def run(self):
        next_t = time.perf_counter()
        while not self._stop.is_set():
            self.tick()
            next_t += self.dt
            lag = next_t - time.perf_counter()
            if lag > 0:
                self._stop.wait(lag)
            else:
                next_t = time.perf_counter()

    def stop(self):
        self._stop.set()