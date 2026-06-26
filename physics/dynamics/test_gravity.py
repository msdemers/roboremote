import pytest

import pathlib
import numpy as np
import pinocchio as pin
from . import dynamics

Z_YAW_Q= "shoulder_pan"

def test_gravity_against_rnea(so101_model):
    model = so101_model
    data = model.createData()

    q_dot = np.zeros(model.nv)
    q_ddot = np.zeros(model.nv)

    for i in range(10):
        q = pin.randomConfiguration(model)
        tau = pin.rnea(model, data, q, q_dot, q_ddot)
        assert np.allclose(dynamics.gravity_compensation(model, data, q), tau, atol=1e-9), "gravity_compensation crosscheck against static pose rnea failed"

def test_gravity_is_zero_along_shoulder_pan(so101_model):
    model = so101_model
    data = model.createData()

    if not model.existJointName(Z_YAW_Q):
        raise ValueError(
            f"Coordinate '{Z_YAW_Q}' does not exist in the loaded model."
        )

    pan_joint_id = model.getJointId(Z_YAW_Q)
    idx_shoulder_pan_v = model.joints[pan_joint_id].idx_v
    nv_shoulder_pan = model.joints[pan_joint_id].nv

    for i in range(10):
        q = pin.randomConfiguration(model)
        g = dynamics.gravity_compensation(model, data, q)
        shoulder_pan_gravity = g[idx_shoulder_pan_v : idx_shoulder_pan_v + nv_shoulder_pan]
        assert np.abs(shoulder_pan_gravity) < 1e-4 * np.max(np.abs(g)), f"gravity contribution to a vertical revolute joint should be near zero, but equals {shoulder_pan_gravity}"
