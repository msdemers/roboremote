from roboremote.arm.v1 import arm_pb2_grpc as pb_grpc
from roboremote.arm.v1 import arm_pb2 as pb
import grpc
from sim.simulator import SimSnapshot, Simulator
from sim import status
from control import controller_factory
import numpy as np
from . import mappers
import time, threading
import logging

class ArmSimServicer(pb_grpc.ArmSimServiceServicer):
    def __init__(self, sim: Simulator, model_name, model_version, publish_hz=120):
        self.sim = sim
        self._descriptor = mappers.build_model_descriptor(sim.model, model_name, model_version)
        self._period = 1.0/publish_hz

    def Subscribe(self, request, context):
        yield pb.StreamEnvelope(descriptor=self._descriptor)

        done = threading.Event()
        context.add_callback(done.set) # allow RPC termination to stop loop imediately

        next_t = time.perf_counter()
        while not done.is_set():
            snapshot = self.sim.get_snapshot()
            yield pb.StreamEnvelope(state=mappers.snapshot_to_arm_state(snapshot))
            next_t += self._period
            lag = next_t - time.perf_counter()
            if lag > 0:
                done.wait(lag) 
            else:
                next_t = time.perf_counter()
    def SetControlMode(self, request, context):
        
        snapshot = self.sim.get_snapshot()
        old_domain = status.domain_for(snapshot.active_mode)
        try:
            control_mode: status.ControlMode = mappers._MODE_MAP_INV[request.mode]
            new_domain = status.domain_for(control_mode)
            target_seed = snapshot.active_target

            if new_domain != old_domain: # target needs to change type. use current robot state for new value
                match new_domain:
                    case status.ControlDomain.JOINT:
                        target_seed = snapshot.q
                    case status.ControlDomain.TASK:
                        target_seed = snapshot.ee_pose
                    case status.ControlDomain.NONE:
                        target_seed = None
            self.sim.set_controller(
                controller_factory.controller_for(control_mode, target_seed)
                )
        except KeyError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"received invalid control mode: {e}")
        except ValueError as e:
            logging.exception("SetControlMode rejected")
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))
        
        return pb.SetControlModeResponse()

    def SetTarget(self, request, context):
        current_controller = self.sim.controller
        target_type = request.WhichOneof("target")
        new_target = None

        match current_controller.mode:
            case status.ControlMode.JOINT_PD_COMPENSATED | status.ControlMode.JOINT_PD_RAW:
                if target_type != "joint_coordinates":
                    context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"joint-space pd controllers require joint Coordinates")
                new_target = np.array(request.joint_coordinates.q)
                if len(new_target) != self.sim.model.nq:
                    context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"target Coordinates.q has nq = {len(new_target)} but expected model.nq = {self.sim.model.nq}")
                self.sim.set_controller(
                    controller_factory.controller_for(current_controller.mode, new_target)
                )
            case status.ControlMode.TASK_PD_COMPENSATED | status.ControlMode.TASK_PD_RAW:
                if target_type != "cartesian_pose":
                    context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"task-space pd controllers require CartesianPose")
                new_target = mappers.cartesian_pose_to_se3(request.cartesian_pose)
                self.sim.set_controller(
                    controller_factory.controller_for(current_controller.mode, new_target)
                )
            case status.ControlMode.GRAVITY_COMP:
                if target_type is not None:
                    context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"control mode does not support targets") 
                # no-op becasue gravity comp controller remains unchanged
        return pb.SetTargetResponse()

    def ResetConfiguration(self, request, context):
        self.sim.reset_configuration()
        return pb.ResetConfigurationResponse()
