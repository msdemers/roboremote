from . import integrator
from dataclasses import dataclass
import numpy as np
import pinocchio as pin
import time, threading

@dataclass(frozen=True)
class SimSnapshot:
    t: float
    q: np.ndarray
    v: np.ndarray
    tau: np.ndarray

class Simulator:
    def __init__(self, model, policy, dt, q0=None, v0=None):
        self.model = model
        self.data = model.createData()
        self.policy = policy
        self.dt = dt
        self.q = (q0 if q0 is not None else pin.neutral(model)).copy()
        self.v = (v0 if v0 is not None else np.zeros(model.nv)).copy()
        self.t = np.zeros(model.nv)
        self.tau = None
        self._stop = threading.Event()

    def tick(self):
        tau = self.policy(self.model, self.data, self.q, self.v)
        self.q, self.v = integrator.step(self.model, self.data, self.q, self.v, tau, self.dt)
        self.tau = tau
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

    def get_snapshot(self) -> SimSnapshot:
        return SimSnapshot(self.t, self.q.copy(), self.v.copy(), self.tau.copy())