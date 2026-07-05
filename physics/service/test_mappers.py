import pytest
import numpy as np
import pinocchio as pin
from roboremote.arm.v1 import arm_pb2 as pb
from service import mappers
from sim.simulator import SimSnapshot, Simulator
from sim import status
import datetime

def test_get_joint_type(so101_model):
    model: pin.Model = so101_model
    pan_joint = model.joints[model.getJointId("shoulder_pan")]

    assert mappers.get_joint_type(pan_joint) == pb.JointInfo.JOINT_TYPE_REVOLUTE, f"unexpected joint type return for {pan_joint.name}"

def test_build_model_descriptor(so101_model):
    model: pin.Model = so101_model
    temp_model_name = model.name + "_testname"
    temp_model_version = str(datetime.datetime.now())

    desc: pb.ModelDescriptor = mappers.build_model_descriptor(model, temp_model_name, temp_model_version)

    assert desc.model_name == temp_model_name, f"model name {desc.model_name} does not match input"
    assert desc.nq == model.nq, f"expected ModelDescriptor to have nq = {model.nq}"
    assert desc.nv == model.nv, f"expected ModelDescriptor to have nv = {model.nv}"
    # the following assertion skips joint 0: Pinocchio's 'universe' root sentinel, which is not a DOF
    assert len(desc.joints) == model.njoints-1, f"expected {model.njoints-1} joints but found {len(desc.joints)}"

    joint_info_shoulder_pan = desc.joints[0]
    assert joint_info_shoulder_pan.name == "shoulder_pan", "first joint failed to match expectations from so-101 arm"
    assert joint_info_shoulder_pan.idx_q == 0, "first joint failed to match expectations from so-101 arm"
    assert joint_info_shoulder_pan.type == pb.JointInfo.JOINT_TYPE_REVOLUTE, "first joint failed to match expectations from so-101 arm"

def test_identity_se3_to_cartesian_pose(so101_model):
    identity_se3: pin.SE3 = pin.SE3.Identity()
    identity_pose: pb.CartesianPose = mappers.se3_to_cartesian_pose(identity_se3)

    assert identity_pose.x == 0.0
    assert identity_pose.y == 0.0
    assert identity_pose.z == 0.0
    assert identity_pose.qx == 0.0
    assert identity_pose.qy == 0.0
    assert identity_pose.qz == 0.0
    assert identity_pose.qw == 1.0

def test_known_se3_to_cartesian_pose(so101_model):
    p = np.array([1.0, 2.0, 3.0])
    theta = np.pi/2
    M: pin.SE3 = pin.SE3(pin.utils.rotate('z', theta), p)
    cartesian_pose: pb.CartesianPose = mappers.se3_to_cartesian_pose(M)

    assert cartesian_pose.x == 1.0
    assert cartesian_pose.y == 2.0
    assert cartesian_pose.z == 3.0
    assert cartesian_pose.qx == 0.0
    assert cartesian_pose.qy == 0.0
    assert cartesian_pose.qz == pytest.approx(np.sqrt(2)/2)
    assert cartesian_pose.qw == pytest.approx(np.sqrt(2)/2)

def test_snapshot_to_armstate_defaults(so101_model):
    model: pin.Model = so101_model
    dt = 0.001
    sim = Simulator(model, dt)
    snap: SimSnapshot = sim.get_snapshot()
    arm_state: pb.ArmState = mappers.snapshot_to_arm_state(snap)
    
    assert arm_state.sim_time == snap.t
    assert np.array_equal(arm_state.q.q, snap.q)
    assert np.array_equal(arm_state.v.v, snap.v)
    assert np.array_equal(arm_state.tau.tau, snap.tau)
    assert arm_state.end_effector.qw == pytest.approx(pin.Quaternion(snap.ee_pose.rotation).w) 
    assert arm_state.status == pb.ARM_STATUS_IDLE
    assert arm_state.active_mode == pb.CONTROL_MODE_GRAVITY_COMP
    assert arm_state.WhichOneof("active_target") is None

def test_snapshot_to_armstate_targets(so101_model):
    model: pin.Model = so101_model
    dt = 0.001
    sim = Simulator(model, dt)

    joint_q = 0.1*np.ones(model.nq)
    sim.active_target = joint_q
    snap: SimSnapshot = sim.get_snapshot()
    arm_state: pb.ArmState = mappers.snapshot_to_arm_state(snap)
    assert arm_state.WhichOneof("active_target") == "joint_target"
    assert np.array_equal(arm_state.joint_target.q, joint_q)

    p = np.array([1.0, 2.0, 3.0])
    theta = np.pi/2
    cartesian_pose: pin.SE3 = pin.SE3(pin.utils.rotate('z', theta), p)
    quat = pin.Quaternion(cartesian_pose.rotation)
    sim.active_target = cartesian_pose
    snap: SimSnapshot = sim.get_snapshot()
    arm_state: pb.ArmState = mappers.snapshot_to_arm_state(snap)
    assert arm_state.WhichOneof("active_target") == "cartesian_target"
    assert np.array_equal(np.array([arm_state.cartesian_target.x, arm_state.cartesian_target.y, arm_state.cartesian_target.z]), p)
    assert np.array_equal(
        np.array([arm_state.cartesian_target.qx, arm_state.cartesian_target.qy, arm_state.cartesian_target.qz, arm_state.cartesian_target.qw]),
        np.array([quat.x, quat.y, quat.z, quat.w]))


