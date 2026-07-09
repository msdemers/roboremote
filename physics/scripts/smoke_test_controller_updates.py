import grpc
from roboremote.arm.v1 import arm_pb2 as pb, arm_pb2_grpc as pb_grpc
import numpy as np

stub = pb_grpc.ArmSimServiceStub(grpc.insecure_channel("localhost:50051"))
nq = None
for i, envelope in enumerate(stub.Subscribe(pb.SubscribeRequest())):
    if envelope.WhichOneof("payload") == "descriptor":
        nq = envelope.descriptor.nq
        continue
    st = envelope.state
    print(i, "mode:", st.active_mode, st.WhichOneof("active_target"))
    print("    q =", list(st.q.q))

    # if we've been running for a sec
    if i == 5:
        stub.SetControlMode(pb.SetControlModeRequest(mode=pb.CONTROL_MODE_JOINT_PD_COMPENSATED))
    # if we've been running for another quick sec
    if i == 15:
        stub.SetTarget(pb.SetTargetRequest(joint_coordinates=pb.Coordinates(q=list(0.1*np.ones(nq)))))
    if i > 30:
        stub.SetControlMode(pb.SetControlModeRequest(mode=pb.CONTROL_MODE_GRAVITY_COMP))
    if i > 45:
        stub.ResetConfiguration(pb.ResetConfigurationRequest())
    if i > 50:
        break