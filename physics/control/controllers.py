import dynamics.dynamics as dyn
import pinocchio as pin
import numpy as np
from typing import Protocol
from sim.status import ControlMode

class Controller(Protocol):
    mode: ControlMode
    target: np.ndarray | pin.SE3 | None
    def compute(self, model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray) -> np.ndarray: ...
        # how do I communicate that this class and method are abstract?

class GravityCompensationController:
    mode = ControlMode.GRAVITY_COMP
    target = None
    def compute(self, model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        return dyn.gravity_compensation(model, data, q)

class JointPdController:
    mode = ControlMode.JOINT_PD_COMPENSATED
    def __init__(self, target: np.ndarray, kp=50.0, kd=5.0):
        self.target = target
        self.kp, self.kd = kp, kd
    def compute(self, model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        gravity_comp = dyn.gravity_compensation(model, data, q)
        q_error = pin.difference(model, q, self.target)
        return self.kp*q_error - self.kd*v + gravity_comp

class JointRawPdController:
    mode = ControlMode.JOINT_PD_RAW
    def __init__(self, target: np.ndarray, kp=50.0, kd=5.0):
        self.target = target
        self.kp, self.kd = kp, kd
    def compute(self, model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        q_error = pin.difference(model, q, self.target)
        return self.kp*q_error - self.kd*v