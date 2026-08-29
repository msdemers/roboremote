import argparse, logging, os, sys
import numpy as np
from pathlib import Path
import pinocchio as pin
from pinocchio.visualize import ViserVisualizer
import viser
import grpc
from roboremote.arm.v1 import arm_pb2
from roboremote.arm.v1 import arm_pb2_grpc as pb_grpc

DEFAULT_REFRESH_RATE = arm_pb2.STREAM_RATE_60

def run_client():
    parser = argparse.ArgumentParser()
    parser.add_argument("address", nargs="?", default=None)
    parser.add_argument("--rate", type=int, choices=[30, 60, 120], default=60)
    parser.add_argument("--open", action="store_true", default=False)
    args = parser.parse_args()

    dial_address, address_source = resolve_addr(args)
    default_model_path = Path(__file__).parent.parent.resolve() / "models/so101/so101_new_calib.urdf"
    model_path = Path(os.getenv("ROBOREMOTE_MODEL_PATH") or default_model_path)
    stream_rate = resolve_refresh_rate(args)

    
    with grpc.insecure_channel(dial_address) as channel:
        stub = pb_grpc.ArmSimServiceStub(channel)

        request = arm_pb2.SubscribeRequest(rate=stream_rate)

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

            # build and load pinocchio's wrapper around Viser
            visualizer = ViserVisualizer(model, collision_model, visual_model)
            visualizer.initViewer(open=False, host="0.0.0.0", port=8080, loadModel=False)
            
            # direct access to Viser's ViserServer
            vServer: viser.ViserServer = visualizer.viewer
            
            # configure viewer details
            vServer.gui.configure_theme(show_logo=False)
            vServer.initial_camera.position = 0.5 * np.ones(3)
            vServer.scene.add_grid(
                "/grid",
                infinite_grid=True,
                cell_size=0.05,
                section_size=0.25,
                position=(
                    0.0, 0.0, 0.0,
                )
            )
            vServer.gui.main_panel.minimize()
            visualizer.loadViewerModel(rootNodeName=model.name)

            if args.open:
                import webbrowser
                webbrowser.open("http://localhost:8080")
            

            for envelope in response_stream:
                arm_state: arm_pb2.ArmState = envelope.state
                #print(f"[{arm_state.sim_time}] q = {arm_state.q.q}")
                visualizer.display(q=np.asarray(arm_state.q.q))

        except grpc.RpcError as e:
            logging.error(f"gRPC stream connection failed: {e.code()} - {e.details()}")
            sys.exit(1)

def resolve_addr(args) -> tuple[str, str]:
    if args.address:
        return args.address, "argument"
    if env_addr := os.getenv("ROBOREMOTE_SERVER_ADDR"):
        return env_addr, "ROBOREMOTE_SERVER_ADDR"
    return "localhost:50051", "default"

def resolve_refresh_rate(args) -> arm_pb2.StreamRate:
    match args.rate:
        case 30:
            return arm_pb2.STREAM_RATE_30
        case 60:
            return arm_pb2.STREAM_RATE_60
        case 120:
            return arm_pb2.STREAM_RATE_120
        case _:
            return arm_pb2.STREAM_RATE_60

if __name__ == "__main__":
    print("=== Starting 3D Visualizer ===")
    logging.basicConfig(level=logging.INFO)
    run_client()

