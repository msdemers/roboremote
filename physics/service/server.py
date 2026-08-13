import os, sys
import time, threading
import pinocchio as pin
from sim.simulator import Simulator
from concurrent import futures
import grpc
from grpc_reflection.v1alpha import reflection
from roboremote.arm.v1 import arm_pb2
from roboremote.arm.v1 import arm_pb2_grpc as pb_grpc
from .servicer import ArmSimServicer


def serve():
    bind_address = _require_env("ROBOREMOTE_PHYSICS_BIND_ADDR", "localhost:50052")

    model_path = _require_env("ROBOREMOTE_MODEL_PATH", "models/so101/so101_new_calib.urdf")

    model_version = "placeholder for hash"
    dt = 0.001

    # start physics sim daemon
    model: pin.Model = pin.buildModelFromUrdf(str(model_path))
    model_name = model.name
    sim = Simulator(model, dt)
    threading.Thread(target=sim.run, daemon=True).start()

    # setup gRPC
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    pb_grpc.add_ArmSimServiceServicer_to_server(ArmSimServicer(sim, model_name, model_version), server)
    server.add_insecure_port(bind_address)

    # register schema in order to support reflection service
    service_names = (
        arm_pb2.DESCRIPTOR.services_by_name["ArmSimService"].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(service_names, server)

    # service lifecycle
    server.start()
    print(f"physics sidecar listening on {bind_address}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        sim.stop()
        server.stop(2.0) # wait a grave period to allow sim loop to stop


def _require_env(name: str, example: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"CRITICAL: {name} is not set. Example: export {name}={example}")
    return value