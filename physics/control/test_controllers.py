import pinocchio as pin
import numpy as np
from . import controllers
from kinematics import forward

def test_compensated_joint_pd_hold_at_target_with_gravity(so101_model):
    model: pin.Model = so101_model
    data: pin.Data = model.createData()

    q_des = 0.3*np.ones(model.nq) # a non-neutral but deterministic pose
    v = np.zeros(model.nv)
    pdContr = controllers.JointPdController(target=q_des)
    tau = pdContr.compute(model, data, q_des, v)
    g = pin.computeGeneralizedGravity(model, model.createData(), q_des)
    assert np.allclose(tau, g), "compensated joint pd effort at static pose should equal gravity"

def test_raw_joint_pd_zero_torque_at_target(so101_model):
    model: pin.Model = so101_model
    data: pin.Data = model.createData()

    q_des = 0.3*np.ones(model.nq) # a non-neutral but deterministic pose
    v = np.zeros(model.nv)
    pdContr = controllers.JointRawPdController(target=q_des)
    tau = pdContr.compute(model, data, q_des, v)
    assert np.allclose(tau, np.zeros(model.nv)), "raw joint pd should generate zero effort at the target pose"
    
def test_raw_joint_pd_weights_error_by_inertia(so101_model):
    model: pin.Model = so101_model
    data: pin.Data = model.createData()

    q_current = 0.2*np.ones(model.nq)
    q_des = 0.3*np.ones(model.nq) # a non-neutral but deterministic pose
    v = np.zeros(model.nv)
    pdContr = controllers.JointRawPdController(target=q_des)
    tau = pdContr.compute(model, data, q_current, v)

    # compute inertia-scaled effort via independent route
    error = pin.difference(model, q_current, q_des)
    M = pin.crba(model, model.createData(), q_current) # compact upper triangular rep
    M = np.triu(M) + np.triu(M, 1).T # build full matrix rep
    expected = M @ (pdContr.kp*error)
    assert np.allclose(tau, expected)

def test_compendated_joint_pd_weights_error_by_inertia(so101_model):
    model: pin.Model = so101_model
    data: pin.Data = model.createData()

    q_current = 0.2*np.ones(model.nq)
    q_des = 0.3*np.ones(model.nq) # a non-neutral but deterministic pose
    v = np.zeros(model.nv)
    pdContr = controllers.JointPdController(target=q_des)
    tau = pdContr.compute(model, data, q_current, v)

    # compute inertia-scaled effort via independent route
    error = pin.difference(model, q_current, q_des)
    M = pin.crba(model, model.createData(), q_current) # compact upper triangular rep
    M = np.triu(M) + np.triu(M, 1).T # build full matrix rep
    expected = M @ (pdContr.kp*error) + pin.computeGeneralizedGravity(model, model.createData(), q_current)
    assert np.allclose(tau, expected)

def test_raw_task_pd_zero_torque_at_target(so101_model):
    model: pin.Model = so101_model
    data: pin.Data = model.createData()

    q_des = 0.3*np.ones(model.nq) # a non-neutral but deterministic pose
    v = np.zeros(model.nv)
    ee_target: pin.SE3 = forward.end_effector_pose(model, data, q_des)

    pdContr = controllers.TaskRawPdController(target=ee_target)
    tau = pdContr.compute(model, data, q_des, v)
    assert np.allclose(tau, np.zeros(model.nv)), "raw task pd should generate zero effort at the target pose"