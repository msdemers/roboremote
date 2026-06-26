import numpy as np
import pinocchio as pin

def step(model: pin.Model,
    data: pin.Data,
    q: np.ndarray,
    v: np.ndarray,
    tau: np.ndarray,
    dt: float,
    f_ext: list[pin.Force] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """
    Advances the robot state by one timestep using semi-implicit (symplectic) Euler integration.
    """

    # compute joint accelerations using pinocchio's articulated body algorithm
    # chose the aba signature based on whether or not we're applying external forces
    if f_ext is None:
        ddq = pin.aba(model, data, q, v, tau)
    else:
        ddq = pin.aba(model, data, q, v, tau, f_ext)

    # integrate velocity
    v_next = v + ddq * dt

    # integrate coordinates using the exponential map from velocity tanget space to the coordinate manifold
    q_next = pin.integrate(model, q, v_next * dt)

    return q_next, v_next