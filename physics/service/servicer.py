from roboremote.arm.v1 import arm_pb2_grpc as pb_grpc
from roboremote.arm.v1 import arm_pb2 as pb
from sim.simulator import SimSnapshot, Simulator
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
