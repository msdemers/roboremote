from roboremote.arm.v1 import arm_pb2_grpc as pb_grpc
from roboremote.arm.v1 import arm_pb2 as pb
import grpc
from sim.simulator import SimSnapshot, Simulator
from sim import status
from control import controller_factory
from . import mappers
import time, threading

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
        try:
            control_mode: status.ControlMode = mappers._MODE_MAP_INV[request.mode]
            match control_mode:
                case status.ControlMode.JOINT_PD_COMPENSATED | status.ControlMode.JOINT_PD_RAW:
                    target_seed = snapshot.q
                case status.ControlMode.TASK_PD_COMPENSATED | status.ControlMode.TASK_PD_RAW:
                    target_seed = snapshot.ee_pose
                case _:
                    target_seed = None
            self.sim.set_controller(
                controller_factory.controller_for(control_mode, target_seed)
                )
        except KeyError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"received invalid control mode: {e}")
        except ValueError as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, f"unsupported control mode: {e}")
        
        pb.SetControModeResponse()
