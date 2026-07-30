package simclient

import (
	"context"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Client struct {
	conn *grpc.ClientConn
	ctx  context.Context
	stub armv1.ArmSimServiceClient
}

func New(ctx context.Context, address string) (*Client, error) {
	serverConn, err := grpc.NewClient(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}

	serviceClient := armv1.NewArmSimServiceClient(serverConn)

	return &Client{
		conn: serverConn,
		ctx:  ctx,
		stub: serviceClient,
	}, nil
}

func (c *Client) Close() error {
	if err := c.conn.Close(); err != nil {
		return err
	}
	return nil
}
