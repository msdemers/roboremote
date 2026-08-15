import grpc
import sys
import os
from grpc_health.v1 import health_pb2, health_pb2_grpc 
ch = grpc.insecure_channel(f"localhost:{os.environ['ROBOREMOTE_PHYSICS_PORT']}")
resp = health_pb2_grpc.HealthStub(ch).Check(health_pb2.HealthCheckRequest(), timeout=2)
sys.exit(0 if resp.status == health_pb2.HealthCheckResponse.SERVING else 1)