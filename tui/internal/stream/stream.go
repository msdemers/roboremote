package stream

import (
	"context"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type Frame struct {
	Envelope *armv1.StreamEnvelope // nil if Err != nil
	Err      error
}

func Connect(ctx context.Context, addr string, streamrate armv1.StreamRate) (<-chan Frame, error) {
	serverConn, err := grpc.NewClient(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}

	serviceClient := armv1.NewArmSimServiceClient(serverConn)
	upstream, err := serviceClient.Subscribe(ctx, &armv1.SubscribeRequest{Rate: streamrate})
	if err != nil {
		serverConn.Close()
		return nil, err
	}

	frames := make(chan Frame)
	go func() {
		defer serverConn.Close()
		for {
			envelope, err := upstream.Recv()
			if err != nil {
				frames <- Frame{Err: err} // since this blocks, needs fix for tear down and reconnect logic to ever land
				close(frames)
				return
			}
			frames <- Frame{Envelope: envelope}
		}
	}()
	return frames, nil
}
