from . import integrator, status
from control import controllers
from kinematics import forward
from dataclasses import dataclass
import numpy as np
import pinocchio as pin
import time, threading
from typing import Union, Optional

@dataclass(frozen=True, eq=False)
class SimSnapshot:
    t: float
    q: np.ndarray
    v: np.ndarray
    tau: np.ndarray
    ee_pose: pin.SE3
    sim_status: status.SimStatus
    active_mode: status.ControlMode
    active_target: Optional[Union[np.ndarray, pin.SE3]]

    def __eq__(self, other):
        if not isinstance(other, SimSnapshot):
            return NotImplemented
        return (
            self.t == other.t
            and np.array_equal(self.q, other.q)
            and np.array_equal(self.v, other.v)
            and np.array_equal(self.tau, other.tau)
        )

class Simulator:
    def __init__(self, model, dt, controller: controllers.Controller | None = None, q0=None, v0=None):
        self.model = model
        self.data = model.createData()
        self.dt = dt
        self.controller = controllers.GravityCompensationController() if controller is None else controller
        self.q = (q0 if q0 is not None else pin.neutral(model)).copy()
        self.v = (v0 if v0 is not None else np.zeros(model.nv)).copy()
        self.ee_pose = forward.end_effector_pose(self.model, self.data, self.q)
        self.sim_status = status.SimStatus.IDLE
        self.t = 0.0
        self.tau = np.zeros(model.nv)
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def tick(self):
        with self._lock:
            model, q, v, dt, controller = self.model, self.q, self.v, self.dt, self.controller
        tau = controller.compute(model, self.data, q, v)
        q_next, v_next = integrator.step(model, self.data, q, v, tau, dt)
        ee_pose = forward.end_effector_pose(model, self.data, q_next)
        with self._lock:
            self.q = q_next
            self.v = v_next
            self.tau = tau
            self.ee_pose = ee_pose
            self.t += dt
        

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
        with self._lock:
            return SimSnapshot(
                self.t, 
                self.q.copy(), 
                self.v.copy(), 
                self.tau.copy(), 
                self.ee_pose.copy(), 
                self.sim_status, 
                self.controller.mode, 
                None if self.controller.target is None else self.controller.target.copy()
            )

    def set_controller(self, controller: controllers.Controller) -> None:
        with self._lock:
            self.controller = controller