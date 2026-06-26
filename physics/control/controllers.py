import dynamics.dynamics as dyn
import kinematics.forward as fwd
import pinocchio as pin
import numpy as np

def gravity_compensation_policy(model: pin.Model, data: pin.Data, q, v) -> np.ndarray:
    return dyn.gravity_compensation(model, data, q)

def zero_control_policy(model: pin.Model, data: pin.Data, q, v) -> np.ndarray:
    return np.zeros(model.nv)