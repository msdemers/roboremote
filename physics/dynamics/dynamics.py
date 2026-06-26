import numpy as np
import pinocchio as pin

def gravity_compensation(model: pin.Model, data: pin.Data, q: np.ndarray):
    """Joint torques that exactly counteract gravity at configuration q.
    Returns τ = g(q), shape (model.nv,), units Nm."""
    return pin.computeGeneralizedGravity(model, data, q)