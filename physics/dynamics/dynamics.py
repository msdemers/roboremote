import numpy as np
import pinocchio as pin

def compute_system_energy(model: pin.Model, data: pin.Data, q: np.ndarray, v: np.ndarray):
    return pin.computeKineticEnergy(model, data, q, v) + pin.computePotentialEnergy(model, data, q)

def gravity_compensation(model: pin.Model, data: pin.Data, q: np.ndarray) -> np.ndarray:
    """Joint torques that exactly counteract gravity at configuration q.
    Returns τ = g(q), shape (model.nv,), units Nm."""
    return pin.computeGeneralizedGravity(model, data, q)

