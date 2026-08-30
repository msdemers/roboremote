import argparse, logging, os, sys
import numpy as np
from pathlib import Path
import pinocchio as pin
from pinocchio.visualize import ViserVisualizer
import viser
import grpc
from roboremote.arm.v1 import arm_pb2
from roboremote.arm.v1 import arm_pb2_grpc as pb_grpc

PHI = 0.5*(1 + 5**0.5) # golden ratio
EE_MARKER_RADIUS = 0.003 # meters
TARGET_CROSSHAIR_AXIS_LENGTH = (PHI**2)*EE_MARKER_RADIUS
TARGET_CROSSHAIR_HOLLOW = PHI*EE_MARKER_RADIUS
TARGET_CROSSHAIR_THICKNESS = 3 # in screen units

CAMERA_UP = (0,0,1)
CAMERA_FOV = 35*np.pi/180 # radians
CAMERA_POSITION = (0.6, 0.6, 0.7)
CAMERA_LOOKAT = (0.3, 0.0, 0.2)

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
            vServer.initial_camera.up = CAMERA_UP
            vServer.initial_camera.fov = CAMERA_FOV
            vServer.initial_camera.position = CAMERA_POSITION
            vServer.initial_camera.look_at = CAMERA_LOOKAT
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

            # create and store handles to computed geometry
            h_ee_marker = add_end_effector_marker(vServer, radius=EE_MARKER_RADIUS)
            h_target_crosshair = add_target_crosshair(vServer, 
                axis_length=TARGET_CROSSHAIR_AXIS_LENGTH, 
                hollow_radius=TARGET_CROSSHAIR_HOLLOW,
                thickness=TARGET_CROSSHAIR_THICKNESS,
            )

            if args.open:
                import webbrowser
                webbrowser.open("http://localhost:8080")
            

            for envelope in response_stream:
                arm_state: arm_pb2.ArmState = envelope.state

                visualizer.display(q=np.asarray(arm_state.q.q))
                ee_pose = arm_state.end_effector
                h_ee_marker.position = (ee_pose.x, ee_pose.y, ee_pose.z)

                if arm_state.WhichOneof("active_target") == "cartesian_target":
                    h_ee_marker.visible = True
                    target = arm_state.cartesian_target
                    h_target_crosshair.position = (target.x, target.y, target.z)
                    h_target_crosshair.visible = True
                else:
                    h_ee_marker.visible = False
                    h_target_crosshair.visible = False


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

def add_end_effector_marker(scene_server, radius):
    h_marker = scene_server.add_icosphere(
        name="end_effector_position",
        radius=radius,
        color=(0.0, 1.0, 0.0),
        subdivisions=3,
        scale=1.0,
        wireframe=False,
        opacity=1,
        material="standard", # 'standard', 'toon3', 'toon5'
        flat_shading=False,
        side="front", # 'front', 'back', 'double'
        cast_shadow=True,
        receive_shadow=True,
        wxyz=(1.0, 0.0, 0.0, 0.0),
        position=(0.0, 0.0, 0.0),
        visible=False,
    )
    return h_marker

def add_target_crosshair(scene_server, axis_length, hollow_radius, thickness):
    points = np.array([
        [[hollow_radius, 0, 0], [axis_length, 0, 0]],
        [[-hollow_radius, 0, 0], [-axis_length, 0, 0]],
        [[0, hollow_radius, 0], [0, axis_length, 0]],
        [[0, -hollow_radius, 0], [0, -axis_length, 0]],
        [[0, 0, hollow_radius], [0, 0, axis_length]],
        [[0, 0, -hollow_radius], [0, 0, -axis_length]]
    ])
    h_crosshair = scene_server.add_line_segments(
        name="target_crosshair",
        points=points,
        colors=(1.0, 0.0, 0.0),
        thickness=thickness,
        thickness_units="screen",
        position=(0, 0, 0),
        visible=False
    )
    return h_crosshair

if __name__ == "__main__":
    print("=== Starting 3D Visualizer ===")
    logging.basicConfig(level=logging.INFO)
    run_client()

