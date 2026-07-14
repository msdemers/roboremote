package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/reflection"
)

type armServer struct {
	armv1.UnimplementedArmSimServiceServer
	sidecar armv1.ArmSimServiceClient // upstream
}

func (s *armServer) SetControlMode(
	ctx context.Context,
	req *armv1.SetControlModeRequest,
) (*armv1.SetControlModeResponse, error) {
	return s.sidecar.SetControlMode(ctx, req)
}

func main() {
	physicsAddr := os.Getenv("PHYSICS_SIDECAR_ADDR")
	if physicsAddr == "" {
		physicsAddr = "localhost:50052"
	}

	physConn, err := grpc.NewClient(physicsAddr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to dial the physics sidecar service %v\n", err)
	}
	defer physConn.Close()

	sidecar := armv1.NewArmSimServiceClient(physConn)

	serverAddr := os.Getenv("SERVER_ADDR")
	if serverAddr == "" {
		serverAddr = ":50051"
	}

	listener, err := net.Listen("tcp", serverAddr)
	if err != nil {
		log.Fatalf("Failed to bind to bind server to port: %v\n", err)
	}

	fmt.Printf("Sim relay server is listening on port %v...\n", serverAddr)

	grpcServer := grpc.NewServer()
	defer grpcServer.Stop()

	armv1.RegisterArmSimServiceServer(grpcServer, &armServer{sidecar: sidecar})
	reflection.Register(grpcServer)

	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("Failed to server gRPC: %v\n", err)
	}

}
