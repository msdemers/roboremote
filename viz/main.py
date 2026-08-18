import logging, os, sys
import numpy as np
import pinocchio as pin
from pinocchio.visualize import ViserVisualizer
import grpc
from roboremote.arm.v1 import arm_pb2
from roboremote.arm.v1 import arm_pb2_grpc as pb_grpc

DEFAULT_REFRESH_RATE = arm_pb2.STREAM_RATE_60

def run_client():
    dial_address = _require_env("ROBOREMOTE_SERVER_ADDR", "localhost:50051")
    model_path = _require_env("ROBOREMOTE_MODEL_PATH", "models/so101/so101_new_calib.urdf")


    with grpc.insecure_channel(dial_address) as channel:
        stub = pb_grpc.ArmSimServiceStub(channel)

        request = arm_pb2.SubscribeRequest(rate=DEFAULT_REFRESH_RATE)

        print("Subscribing to stream updates from roboremote server...")
        
        try:
            response_stream = stub.Subscribe(request)
            
            first: arm_pb2.StreamEnvelope = next(response_stream) # first message is the model descriptor by design
            if first.WhichOneof("payload") != "descriptor":
                logging.error("did not receive the model descriptor message.")
                sys.exit(1)
            model_descriptor = first.descriptor

            model, collision_model, visual_model = pin.buildModelsFromUrdf(
                model_path,
                package_dirs=[os.path.dirname(model_path)]
            )

            visualizer = ViserVisualizer(model, collision_model, visual_model)
            visualizer.initViewer(open=True)
            visualizer.loadViewerModel(rootNodeName=model.name)

            for envelope in response_stream:
                arm_state: arm_pb2.ArmState = envelope.state
                #print(f"[{arm_state.sim_time}] q = {arm_state.q.q}")
                visualizer.display(q=np.asarray(arm_state.q.q))

        except grpc.RpcError as e:
            logging.error(f"gRPC stream connection failed: {e.code()} - {e.details()}")
            sys.exit(1)

def _require_env(name: str, example: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(f"CRITICAL: {name} is not set. Example: export {name}={example}")
    return value

if __name__ == "__main__":
    print("=== Starting 3D Visualizer ===")
    logging.basicConfig(level=logging.INFO)
    run_client()

