package app

import (
	"context"
	"errors"

	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"github.com/msdemers/roboremote/tui/internal/stream"
)

func (m model) Init() tea.Cmd {
	return connectToSimStream(m.ctx, m.address, m.streamrate)
}

func connectToSimStream(ctx context.Context, addr string, streamrate armv1.StreamRate) tea.Cmd {
	return func() tea.Msg {
		frames, err := stream.Connect(ctx, addr, streamrate)
		if err != nil {
			return connectedMsg{err: err}
		}
		return connectedMsg{ch: frames}
	}
}

func waitForSimFrame(frames <-chan stream.Frame) tea.Cmd {
	return func() tea.Msg {
		frame, ok := <-frames
		if !ok {
			return disconnectMsg{err: errors.New("stream closed unexpectedly")}
		}

		if frame.Err != nil {
			return disconnectMsg{err: frame.Err}
		}

		switch frame.Envelope.GetPayload().(type) {
		case *armv1.StreamEnvelope_Descriptor_:
			return descriptorMsg{descriptor: frame.Envelope.GetDescriptor_()}
		case *armv1.StreamEnvelope_State:
			return armStateMsg{armState: frame.Envelope.GetState()}
		default:
			return disconnectMsg{err: errors.New("unrecognized frame payload type")}
		}
	}
}
