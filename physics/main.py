# TODO: initialize gRPC physics sidecar
import service.server as server

if __name__ == "__main__":
    print("=== Starting Physics Sidecar ===")
    phys_server = server.serve()
