package simclient

import (
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Client struct {
	conn *grpc.ClientConn
	stub armv1.ArmSimServiceClient
}

func New(address string) (*Client, error) {
	serverConn, err := grpc.NewClient(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}

	serviceClient := armv1.NewArmSimServiceClient(serverConn)

	return &Client{
		conn: serverConn,
		stub: serviceClient,
	}, nil
}
