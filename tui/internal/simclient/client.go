package simclient

import (
	"context"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Client struct {
	address      string
	conn         *grpc.ClientConn
	ctx          context.Context
	stub         armv1.ArmSimServiceClient
	discreteCmds chan queuedCmd
	latestTarget chan *armv1.SetTargetRequest
	results      chan CommandResult
}

func New(ctx context.Context, address string) (*Client, error) {
	serverConn, err := grpc.NewClient(address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}

	serviceClient := armv1.NewArmSimServiceClient(serverConn)

	c := Client{
		address:      address,
		conn:         serverConn,
		ctx:          ctx,
		stub:         serviceClient,
		discreteCmds: make(chan queuedCmd, 8),
		latestTarget: make(chan *armv1.SetTargetRequest, 1),
		results:      make(chan CommandResult, 4),
	}

	go c.pump()
	return &c, nil
}

func (c Client) Address() string {
	return c.address
}

func (c *Client) Close() error {
	if err := c.conn.Close(); err != nil {
		return err
	}
	return nil
}
