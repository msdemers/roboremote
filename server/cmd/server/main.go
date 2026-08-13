package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"github.com/msdemers/roboremote/server/internal/relay"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/reflection"
)

type armServer struct {
	armv1.UnimplementedArmSimServiceServer
	sidecar armv1.ArmSimServiceClient // upstream and commands target
	hub     *relay.Hub                // for snapshot fan-out
}

func (s *armServer) SetControlMode(
	ctx context.Context,
	req *armv1.SetControlModeRequest,
) (*armv1.SetControlModeResponse, error) {
	return s.sidecar.SetControlMode(ctx, req)
}

func (s *armServer) SetTarget(
	ctx context.Context,
	req *armv1.SetTargetRequest,
) (*armv1.SetTargetResponse, error) {
	return s.sidecar.SetTarget(ctx, req)
}

func (s *armServer) ResetConfiguration(
	ctx context.Context,
	req *armv1.ResetConfigurationRequest,
) (*armv1.ResetConfigurationResponse, error) {
	return s.sidecar.ResetConfiguration(ctx, req)
}

func decimationFor(rate armv1.StreamRate) int {
	switch rate {
	case armv1.StreamRate_STREAM_RATE_120:
		return 1
	case armv1.StreamRate_STREAM_RATE_30:
		return 4
	default:
		return 2 // everything else maps to the default 60 Hz
	}
}

func (s *armServer) Subscribe(
	req *armv1.SubscribeRequest,
	stream grpc.ServerStreamingServer[armv1.StreamEnvelope],
) error {
	n := decimationFor(req.GetRate())
	desc, frames, unsubscribe := s.hub.Subscribe(n)
	defer unsubscribe()

	if err := stream.Send(desc); err != nil { // always send model descriptor as first frame to client
		return err
	}
	for {
		select {
		case frame, ok := <-frames:
			if !ok {
				return nil // hub closed the slot for this subscriber
			}
			if err := stream.Send(frame); err != nil {
				return err
			}
		case <-stream.Context().Done():
			return nil // client disconnected
		}
	}
}

func main() {
	physicsAddr := os.Getenv("ROBOREMOTE_PHYSICS_ADDR")
	if physicsAddr == "" {
		physicsAddr = "localhost:50052"
	}

	physConn, err := grpc.NewClient(physicsAddr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Failed to dial the physics sidecar service %v\n", err)
	}
	defer physConn.Close()

	sidecar := armv1.NewArmSimServiceClient(physConn)

	hub := relay.NewHub()
	go hub.Run()
	go func() {
		if err := hub.Pump(context.Background(), sidecar); err != nil {
			log.Printf("pump stopped: %v", err)
		}
	}()

	serverAddr := os.Getenv("ROBOREMOTE_SERVER_BIND_ADDR")
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

	armv1.RegisterArmSimServiceServer(grpcServer, &armServer{sidecar: sidecar, hub: hub})
	reflection.Register(grpcServer)

	if err := grpcServer.Serve(listener); err != nil {
		log.Fatalf("Failed to server gRPC: %v\n", err)
	}

}
