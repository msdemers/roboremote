import pytest

import pathlib
import numpy as np
import pinocchio as pin
from . import forward

TEST_SO101_MODEL = "models/so101/so101_new_calib.urdf"

R_REF_QZERO = np.array([
      [ 8.66502e-06, -1.03004e-05, 1.0        ],
      [ 0.0486629,    0.998815,    9.8665e-06 ],
      [-0.998815,     0.0486629,   9.156e-06  ],
  ])
P_REF_QZERO = np.array([0.391361, -9.21206e-06, 0.22647])
REF_QZERO = pin.SE3(R_REF_QZERO, P_REF_QZERO)

def test_home_config_matches_frozen_golden_ref():
    urdf_path = pathlib.Path(__file__).parents[2] / TEST_SO101_MODEL
    model = pin.buildModelFromUrdf(urdf_path)
    
    data = model.createData()
    q = pin.neutral(model)

    gripper_pose = forward.end_effector_pose(model, data, q)
    
    assert np.allclose(gripper_pose.homogeneous, REF_QZERO.homogeneous, atol=1e-3), f"Gripper frame SE3 at home (q = zeros) fails to match historical values: current SE3 = {gripper_pose}"
    end_effector_z = gripper_pose.rotation[:, 2]
    assert  end_effector_z @ np.array([1, 0, 0]) > np.cos(np.radians(5.0)), f"gripper z fails to point forward (+X) at home: gripper_z = {end_effector_z}"

if __name__ == "__main__":
    # Pass sys.argv so you can pass custom flags like -v or -k from the CLI
    import sys

    sys.exit(pytest.main(sys.argv))
