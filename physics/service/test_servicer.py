from sim.simulator import Simulator
from sim import status
from control import controller_factory
from service.servicer import ArmSimServicer
from roboremote.arm.v1 import arm_pb2 as pb
import grpc
import pytest
import pinocchio as pin
import numpy as np

class Aborted(Exception): pass

class FakeContext:
    def abort(self, code, details):
        self.code, self.details = code, details
        raise Aborted() # note to self: this models gRPC's unwind

def test_set_target_rejected_in_gravity_comp(so101_model):
    sim = Simulator(so101_model, dt=0.001) # defaults to GRAVITY_COMP mode
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    # try to set a target on a gravity comp controller that doesn't allow it
    req = pb.SetTargetRequest(joint_coordinates=pb.Coordinates(q=[0.1]*so101_model.nq))
    with pytest.raises(Aborted):
        servicer.SetTarget(req, ctx)
    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT

def test_cartesian_target_rejected_in_joint_pd(so101_model):
    model = so101_model
    sim = Simulator(model, dt=0.001)
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    sim.set_controller(controller_factory.controller_for(
        status.ControlMode.JOINT_PD_COMPENSATED, pin.neutral(model)
    ))
    # try to set cartesian pose while in incompatible joint pd mode
    req = pb.SetTargetRequest(cartesian_pose=pb.CartesianPose(
        x=0.0, y=0.0, z=0.0,
        qx=0.0, qy=0.0, qz=0.0, qw=1.0
    ))
    with pytest.raises(Aborted): servicer.SetTarget(req, ctx)
    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT

def test_joint_target_too_long_gets_rejected(so101_model):
    model = so101_model
    sim = Simulator(model, dt=0.001) 
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    sim.set_controller(controller_factory.controller_for(
        status.ControlMode.JOINT_PD_COMPENSATED, pin.neutral(model)
    ))
    # try to set joint coordinates vector longer than model.nq
    req = pb.SetTargetRequest(joint_coordinates=pb.Coordinates(q=[0.1]*(model.nq+1)))
    with pytest.raises(Aborted): servicer.SetTarget(req, ctx)
    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT

def test_unsupported_mode(so101_model):
    model = so101_model
    sim = Simulator(model, dt=0.001) 
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    # try to set control mode to something unsupported
    req = pb.SetControlModeRequest(mode=100) # not likely to ever have 100 control modes enumerated
    with pytest.raises(Aborted): servicer.SetControlMode(req, ctx)
    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT

def test_unimplemented_mode(so101_model):
    model = so101_model
    sim = Simulator(model, dt=0.001) 
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    # try to set control mode to something unsupported
    req = pb.SetControlModeRequest(mode=pb.ControlMode.CONTROL_MODE_UNSPECIFIED) # not likely to ever have 100 control modes enumerated
    with pytest.raises(Aborted): servicer.SetControlMode(req, ctx)
    assert ctx.code == grpc.StatusCode.INVALID_ARGUMENT

def test_set_joint_target_completes(so101_model):
    model = so101_model
    sim = Simulator(model, dt=0.001) 
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    sim.set_controller(controller_factory.controller_for(
        status.ControlMode.JOINT_PD_COMPENSATED, pin.neutral(model)
    ))
    # try to set legit joint coordinates vector 
    q_des = 0.1*np.ones(model.nq)
    req = pb.SetTargetRequest(joint_coordinates=pb.Coordinates(q=list(q_des)))
    res = servicer.SetTarget(req, ctx)
    assert isinstance(res, pb.SetTargetResponse)
    assert np.allclose(sim.controller.target, q_des)