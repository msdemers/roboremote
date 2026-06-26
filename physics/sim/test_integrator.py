import pytest

import pathlib
import numpy as np
import pinocchio as pin
from . import integrator
import dynamics.dynamics as dyn

INTEGRATOR_STEP_SIZE = 0.001
Q_ERROR_THRESHOLD = 1e-9

def test_static_equilibrium(so101_model):
    """Confirm that forward integration from a static pose with gravity_compensation tau applied results in near zero motion
    """
    model = so101_model
    data = model.createData()

    q_0 = pin.randomConfiguration(model)
    q_next = q_0.copy()
    v_next = np.zeros(model.nv)
    dt = INTEGRATOR_STEP_SIZE
    n_steps = 5000

    for k in range(n_steps):
        tau_gravity = dyn.gravity_compensation(model, data, q_next)
        q_next, v_next = integrator.step(model, data, q_next, v_next, tau_gravity, dt)
        
    assert np.allclose(q_next, q_0, 0.0, atol=Q_ERROR_THRESHOLD), "static pose simulation should not have changed configuration"
    assert np.allclose(v_next, np.zeros(model.nv), 0.0, atol=Q_ERROR_THRESHOLD), "static pose simulation should have velocity of zero"


def test_passive_energy_conservation(so101_model):
    """Confirm that forward integration from any pose with no actuation and no external forces conserves system energy.
    """
    model = so101_model
    data = model.createData()

    q_0 = pin.neutral(model)
    v_0 = np.zeros(model.nv)
    tau_0 = np.zeros(model.nv)
    E_0 = dyn.compute_system_energy(model, data, q_0, v_0)
    
    T = 0.5
    dt_settings = [INTEGRATOR_STEP_SIZE, INTEGRATOR_STEP_SIZE/2.0, INTEGRATOR_STEP_SIZE/4.0]
    error_bands = np.zeros(np.shape(dt_settings))
    
    for i, dt in enumerate(dt_settings):
        
        n_steps = np.ceil(T/dt).astype(int)
        E_history = np.zeros(n_steps)
        q_next = q_0.copy()
        v_next = v_0.copy()

        for k in range(n_steps):
            q_next, v_next = integrator.step(model, data, q_next, v_next, tau_0, dt)
            E_history[k] = dyn.compute_system_energy(model, data, q_next, v_next)
        
        max_energy_err = np.max(np.abs(E_history - E_0))
        error_bands[i] = max_energy_err
        # check that energy error converges approximately proportional to dt step size
        if i > 0:
            dtRatio = dt_settings[i]/dt_settings[i-1]
            convRatio = error_bands[i]/error_bands[i-1]

            assert convRatio > 0.7*dtRatio and convRatio < 1.25*dtRatio, f"expected energy convergence ratio {convRatio} to be approximately equal to the time convergence ratio {dtRatio}"

def test_step_does_not_mutate_state(so101_model):
    """Confirm that forward integration step method returns new states and does NOT mutate the input states.
    """
    model = so101_model
    data = model.createData()

    q_0 = pin.neutral(model)
    v_0 = np.zeros(model.nv)
    tau_0 = np.zeros(model.nv)
    dt_0 = np.float16(0.001)

    q, v, tau, dt = q_0.copy(), v_0.copy(), tau_0.copy(), dt_0.copy()
    integrator.step(model, data, q, v, tau, dt)
    assert np.array_equal(q, q_0) and np.array_equal(v, v_0) and np.array_equal(tau, tau_0) and dt == dt_0, "step must not mutate its inputs"