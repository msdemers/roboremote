package simclient

import (
	"context"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

type Frame struct {
	Envelope *armv1.StreamEnvelope // nil if Err != nil
	Err      error
}

func (c *Client) Subscribe(ctx context.Context, streamrate armv1.StreamRate) (<-chan Frame, error) {
	upstream, err := c.stub.Subscribe(ctx, &armv1.SubscribeRequest{Rate: streamrate})
	if err != nil {
		c.conn.Close()
		return nil, err
	}

	frames := make(chan Frame)
	go func() {
		defer c.conn.Close()
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
