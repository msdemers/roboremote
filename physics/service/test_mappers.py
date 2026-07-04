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