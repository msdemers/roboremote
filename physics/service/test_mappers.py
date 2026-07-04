import pytest
import numpy as np
import pinocchio as pin
from roboremote.arm.v1 import arm_pb2 as pb
from service import mappers
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
