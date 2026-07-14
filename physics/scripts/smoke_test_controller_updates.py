import grpc
from roboremote.arm.v1 import arm_pb2 as pb, arm_pb2_grpc as pb_grpc
import numpy as np

def pretty_print_row(row_vec, sig_figs=4, width=12, prefix=""):
    formatted_row = [f"{item:> {width}.{sig_figs}g}" for item in row_vec]
    print(prefix + " ".join(formatted_row))

stub = pb_grpc.ArmSimServiceStub(grpc.insecure_channel("localhost:50052"))
nq = None
for i, envelope in enumerate(stub.Subscribe(pb.SubscribeRequest())):
    if envelope.WhichOneof("payload") == "descriptor":
        nq = envelope.descriptor.nq
        continue
    st = envelope.state
    print(i, "mode:", st.active_mode, st.WhichOneof("active_target"))
    pretty_print_row(list(st.q.q), sig_figs=4, width=10, prefix="  q =")
    ee_position = [st.end_effector.x, st.end_effector.y, st.end_effector.z]
    pretty_print_row(ee_position, sig_figs=4, width=10, prefix="  ee position =")

    # if we've been running for a sec
    if i == 5:
        stub.SetControlMode(pb.SetControlModeRequest(mode=pb.CONTROL_MODE_JOINT_PD_COMPENSATED))
    # if we've been running for another quick sec
    if i == 15:
        stub.SetTarget(pb.SetTargetRequest(joint_coordinates=pb.Coordinates(q=list(0.1*np.ones(nq)))))
    if i == 30:
        stub.SetControlMode(pb.SetControlModeRequest(mode=pb.CONTROL_MODE_TASK_PD_COMPENSATED))
    if i == 40:
        stub.SetTarget(pb.SetTargetRequest(
            cartesian_pose=pb.CartesianPose(x=0.2, y=0.2, z=0.2, qx=0.0, qy=0.0, qz=0.0, qw=1.0)))
    if i == 50:
        stub.SetControlMode(pb.SetControlModeRequest(mode=pb.CONTROL_MODE_TASK_PD_RAW))
    if i > 60:
        stub.SetControlMode(pb.SetControlModeRequest(mode=pb.CONTROL_MODE_GRAVITY_COMP))
    if i > 70:
        stub.ResetConfiguration(pb.ResetConfigurationRequest())
    if i > 75:
        break