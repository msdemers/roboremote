package relay

import (
	"context"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

type subscriber struct {
	frames chan *armv1.StreamEnvelope
	desc   chan *armv1.StreamEnvelope
}

type Hub struct {
	register   chan *subscriber
	unregister chan *subscriber
	frames     chan *armv1.StreamEnvelope
}

func NewHub() *Hub {
	return &Hub{
		register:   make(chan *subscriber),
		unregister: make(chan *subscriber),
		frames:     make(chan *armv1.StreamEnvelope),
	}
}

func (h *Hub) Run() {
	subs := map[*subscriber]struct{}{}
	var descriptor *armv1.StreamEnvelope
	var pending []*subscriber

	for {
		select {
		case s := <-h.register:
			subs[s] = struct{}{}
			if descriptor != nil {
				s.desc <- descriptor
			} else {
				pending = append(pending, s)
			}
		case s := <-h.unregister:
			delete(subs, s)
			close(s.frames) // end the client handler's reveive loop
		case frame := <-h.frames:
			if descriptor == nil { // the first frame will be the model descriptor
				descriptor = frame // cache it to provide to each subscriber client
				for _, s := range pending {
					s.desc <- descriptor
				}
				pending = nil
				continue
			}
			// fan out frame to all live clients
			for s := range subs {
				// latest-wins send
				select {
				case s.frames <- frame: // s.frames was empty. give it the fresh frame
				default:
					// s.frames is full. Evict stale frame and insert fresh one
					select {
					case <-s.frames: // evict stale s.frames
					default: // do nothing
					}
					s.frames <- frame
				}
			}
		}
	}
}

func (h *Hub) Subscribe() (desc *armv1.StreamEnvelope, frames <-chan *armv1.StreamEnvelope, unsubscribe func()) {
	s := &subscriber{
		frames: make(chan *armv1.StreamEnvelope, 1), // latest-wins snapshot slot
		desc:   make(chan *armv1.StreamEnvelope, 1), //
	}
	h.register <- s                            // blocks until h.run() accepts
	desc = <-s.desc                            // run() provides the cached descriptor
	unsubscribe = func() { h.unregister <- s } // unsubscribe by unregistering from hub's map
	return desc, s.frames, unsubscribe
}

func (h *Hub) Pump(ctx context.Context, client armv1.ArmSimServiceClient) error {
	upstream, err := client.Subscribe(ctx, &armv1.SubscribeRequest{})
	if err != nil {
		return err
	}
	for {
		envelope, err := upstream.Recv()
		if err != nil {
			return err // EOF or failure
		}
		h.frames <- envelope
	}
}
