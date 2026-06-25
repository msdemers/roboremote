import pytest

import pathlib
import numpy as np
import pinocchio as pin
from . import dynamics

TEST_SO101_MODEL = "models/so101/so101_new_calib.urdf"

def test_gravity_against_rnea():
    urdf_path = pathlib.Path(__file__).parents[2] / TEST_SO101_MODEL
    model = pin.buildModelFromUrdf(urdf_path)
    
    data = model.createData()

    q_dot = np.zeros(model.nv)
    q_ddot = np.zeros(model.nv)

    for i in range(10):
        q = pin.randomConfiguration(model)
        tau = pin.rnea(model, data, q, q_dot, q_ddot)
        assert np.allclose(dynamics.gravity_compensation(model, data, q), tau, atol=1e-9), "todo: message"

