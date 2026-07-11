import dynamics.dynamics as dyn
from kinematics import forward
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
    def __init__(self, target: np.ndarray, kp=2500.0, kd=100.0):
        self.target = target
        self.kp, self.kd = kp, kd
    def compute(self, model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        q_error = pin.difference(model, q, self.target)
        a_des = self.kp*q_error - self.kd*v
        return pin.rnea(model, data, q, v, a_des)

class JointRawPdController:
    mode = ControlMode.JOINT_PD_RAW
    def __init__(self, target: np.ndarray, kp=2500.0, kd=100.0):
        self.target = target
        self.kp, self.kd = kp, kd
    def compute(self, model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        q_error = pin.difference(model, q, self.target)
        a_des = self.kp*q_error - self.kd*v
        tau_full = pin.rnea(model, data, q, v, a_des)
        b = pin.nonLinearEffects(model, data, q, v) # coriolis and gravity effects
        return tau_full - b

class TaskRawPdController:
    mode = ControlMode.TASK_PD_RAW
    def __init__(self, target: pin.SE3, kp=2500.0, kd=100.0, lam=0.3, kn=0.015):
        self.target = target
        self.kp, self.kd = kp, kd
        self.lam = lam
        self.kn = kn
    def compute(self, model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        J = pin.computeFrameJacobian(model, data, q, forward.EE_FRAME, pin.LOCAL_WORLD_ALIGNED)
        # for now, task space control is positional control only (no attitude control)
        J_pos = J[:3]
        e_x = self.target.translation - forward.end_effector_pose(model, data, q).translation
        v_x = J_pos @ v
        a_x = self.kp*e_x - self.kd*v_x

        M_inv = pin.computeMinverse(model, data, q)
        A = J_pos @ M_inv @ J_pos.T + (self.lam)**2*np.eye(3)

        Lambda = np.linalg.inv(A) # compute Lambda = inv(A)
        
        # control in the task space
        F = Lambda @ a_x 

        # construct damping in the null-space
        J_conj_T = Lambda @ J_pos @ M_inv
        N = np.eye(model.nv) - (J_pos.T @ J_conj_T) # the null-space projector
        # decouple null-space damping from the light and slow-moving gripper length
        N[:,model.nv-1] = 0.0
        N[model.nv-1,:] = 0.0
        tau_null = N @ (-self.kn*v) # damping in the null space
        tau = J_pos.T @ F + tau_null
        return tau


        



