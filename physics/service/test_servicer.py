from sim.simulator import Simulator
from sim import status
from control import controller_factory
import operator
import service.mappers as mappers
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

def test_joint_target_rejected_in_task_pd(so101_model):
    model = so101_model
    sim = Simulator(model, dt=0.001)
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    sim.set_controller(controller_factory.controller_for(
        status.ControlMode.TASK_PD_COMPENSATED, sim.ee_pose
    ))
    # try to set joint coordinates in incompatible task pd mode
    req = pb.SetTargetRequest(joint_coordinates=pb.Coordinates(q=[0.1]*model.nq))
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

def test_set_cartesian_target_completes(so101_model):
    model = so101_model
    sim = Simulator(model, dt=0.001)
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()
    sim.set_controller(controller_factory.controller_for(
        status.ControlMode.TASK_PD_COMPENSATED, sim.ee_pose
    )) 
    # try to set legit cartesian end effector target pose
    req = pb.SetTargetRequest(cartesian_pose=pb.CartesianPose(
        x=0.0, y=0.0, z=0.0,
        qx=0.0, qy=0.0, qz=0.0, qw=1.0
    ))
    res = servicer.SetTarget(req,ctx)
    assert isinstance(res, pb.SetTargetResponse)
    assert sim.controller.target.isApprox(pin.SE3.Identity())

@pytest.mark.parametrize("start_mode,new_mode,make_start,make_expected,compare",
[
    pytest.param(
        status.ControlMode.JOINT_PD_COMPENSATED,
        status.ControlMode.JOINT_PD_RAW,
        lambda sim: pin.neutral(sim.model) + 0.08,
        lambda sim, start: start,
        np.allclose,
        id="joint_compensated_to_raw_preserves",
    ),
    pytest.param(
        status.ControlMode.JOINT_PD_COMPENSATED,
        status.ControlMode.TASK_PD_COMPENSATED,
        lambda sim: pin.neutral(sim.model) + 0.08,
        lambda sim, start: sim.ee_pose,
        lambda got, want: got.isApprox(want),
        id="joint_to_task_reseeds_from_ee_pose"
    ),
    pytest.param(
        status.ControlMode.TASK_PD_COMPENSATED,
        status.ControlMode.TASK_PD_RAW,
        lambda sim: pin.SE3.Identity(),
        lambda sim, start: start,
        lambda got, want: got.isApprox(want),
        id="task_compensated_to_raw_preserves"
    ),
    pytest.param(
        status.ControlMode.TASK_PD_COMPENSATED,
        status.ControlMode.JOINT_PD_COMPENSATED,
        lambda sim: pin.SE3.Identity(),
        lambda sim, start: sim.q,
        np.allclose,
        id="task_to_joint_reseeds_from_q",
    ),
    pytest.param(
        status.ControlMode.GRAVITY_COMP,
        status.ControlMode.JOINT_PD_COMPENSATED,
        lambda sim: None,
        lambda sim, start: sim.q,
        np.allclose,
        id="gravity_to_joint_reseeds_from_q",
    ),
    pytest.param(
        status.ControlMode.JOINT_PD_COMPENSATED,
        status.ControlMode.GRAVITY_COMP,
        lambda sim: pin.neutral(sim.model) + 0.08,
        lambda sim, start: None,
        operator.is_,
        id="joint_to_gravity_clears_target",
    ),
])
def test_mode_switch_target_seeding( so101_model, start_mode, new_mode, make_start, make_expected, compare):
    # init sim to nonneutral pose unique from all state/snapshot conditions in the test table
    sim = Simulator(so101_model, dt=0.001, q0=pin.neutral(so101_model) - 0.08)
    servicer = ArmSimServicer(sim, "so101", "v0")
    ctx = FakeContext()

    start = make_start(sim)
    sim.set_controller(
        controller_factory.controller_for(start_mode, start
    ))

    # make and send request to switch control mode
    res = servicer.SetControlMode(
        pb.SetControlModeRequest(mode=mappers._MODE_MAP[new_mode]), 
        ctx,
    )

    assert sim.controller.mode == new_mode
    assert compare(sim.controller.target, make_expected(sim, start))
