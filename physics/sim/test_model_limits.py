from . import model_limits
import numpy as np
import pinocchio as pin
import pytest

def test_interior_pose_unclipped(so101_model):
    model: pin.Model = so101_model
    q = pin.randomConfiguration(model)
    v = np.random.uniform(-2*np.pi, 2*np.pi, model.nv)

    q_clipped, v_clipped = model_limits.clip_joint_rom(model, q, v)
    np.testing.assert_array_equal(q_clipped, q, err_msg="coordinates clipped while within joint coordinate ranges")
    np.testing.assert_array_equal(v_clipped, v, err_msg="velocities clipped while joint coordinates within allowed ranges")

def test_joint_limits_enforced(so101_model):
    model: pin.Model = so101_model
    q = pin.randomConfiguration(model)
    v = np.zeros(model.nv)
    i_upper = 1
    i_lower = 2
    q[i_upper] = model.upperPositionLimit[i_upper] + 0.1
    q[i_lower] = model.lowerPositionLimit[i_lower] - 0.1
    q_clipped, v_clipped = model_limits.clip_joint_rom(model, q, v)

    for i in range(model.nq):
        if i == i_upper:
            assert q_clipped[i] == model.upperPositionLimit[i], "coordinate was not clipped to upper limit"
        elif i == i_lower:
            assert q_clipped[i] == model.lowerPositionLimit[i], "coordinate was not clipped to lower limit"
        else:
            assert q_clipped[i] == q[i], "coordinate was clipped despite being within joint limits"

def test_outward_only_velocities_gated(so101_model):
    model: pin.Model = so101_model
    q = pin.randomConfiguration(model)
    v = np.zeros(model.nv)
    joint: pin.JointModel = model.joints[model.njoints-1]
    i_q = joint.idx_q # joint's first coordinate index
    i_v = joint.idx_v # joint's first velocity index
    
    q[i_q] = model.upperPositionLimit[i_q] + 0.1
    v[i_v] = 1.0 # moving into the upper joint limit
    q_clipped, v_clipped = model_limits.clip_joint_rom(model, q, v)
    assert v_clipped[i_v] == 0, "outbound velocity was not clipped at upper joint limit"
    v[i_v] = -1.0 # moving away from the upper joint limit
    q_clipped, v_clipped = model_limits.clip_joint_rom(model, q, v)
    assert v_clipped[i_v] == v[i_v], "inbound velocity was erroneously clipped at upper joint limit"

    q[i_q] = model.lowerPositionLimit[i_q] - 0.1
    v[i_v] = -1.0 # moving into the lower joint limit
    q_clipped, v_clipped = model_limits.clip_joint_rom(model, q, v)
    assert v_clipped[i_v] == 0, "outbound velocity was not clipped at lower joint limit"
    v[i_v] = 1.0 # moving away from the lower joint limit
    q_clipped, v_clipped = model_limits.clip_joint_rom(model, q, v)
    assert v_clipped[i_v] == v[i_v], "inbound velocity was erroneously clipped at lower joint limit"
      
def test_ensure_non_mutating_joint_limit_clipping(so101_model):
    model: pin.Model = so101_model
    outOfBounds = model.upperPositionLimit + 0.1
    q = np.copy(outOfBounds) # all q outside joint limits
    outwardBound = np.ones(model.nv)
    v = np.copy(outwardBound)
    q_clipped, v_clipped = model_limits.clip_joint_rom(model, q, v)
    np.testing.assert_equal(q,outOfBounds, err_msg="joint-limit clipping mutated the input coordinates q")
    np.testing.assert_equal(v, outwardBound, err_msg="joint-limit clipping mutated the input velocities v")