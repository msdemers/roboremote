import grpc
from roboremote.arm.v1 import arm_pb2 as pb, arm_pb2_grpc as pb_grpc
stub = pb_grpc.ArmSimServiceStub(grpc.insecure_channel("localhost:50052"))
for i, env in enumerate(stub.Subscribe(pb.SubscribeRequest())):
    payload = env.WhichOneof("payload")
    print(i, payload, f"model name: {env.descriptor.model_name}" if payload == "descriptor" else f"t = {env.state.sim_time}" )
    if i > 5: break