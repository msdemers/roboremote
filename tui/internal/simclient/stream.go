package simclient

import (
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

type Frame struct {
	Envelope *armv1.StreamEnvelope // nil if Err != nil
	Err      error
}

func (c *Client) Subscribe(streamRate armv1.StreamRate) (<-chan Frame, error) {
	upstream, err := c.stub.Subscribe(c.ctx, &armv1.SubscribeRequest{Rate: streamRate})
	if err != nil {
		c.conn.Close()
		return nil, err
	}

	frames := make(chan Frame)
	go func() {
		defer close(frames)
		for {
			envelope, err := upstream.Recv()
			if err != nil {
				frames <- Frame{Err: err} // since this blocks, needs fix for tear down and reconnect logic to ever land
				return
			}
			frames <- Frame{Envelope: envelope}
		}
	}()
	return frames, nil
}
