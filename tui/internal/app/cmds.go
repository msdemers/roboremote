package app

import (
	"errors"
	"time"

	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	sim "github.com/msdemers/roboremote/tui/internal/simclient"
)

func (m model) Init() tea.Cmd {
	return tea.Batch(
		subscribeToSimStream(m.sim, m.streamRate),
		waitForCommandResult(m.sim.Results()),
	)

}

func expireConfirmation() tea.Cmd {
	return tea.Tick(confirmationTimeout, func(t time.Time) tea.Msg {
		return confirmationExpiredMsg{}
	})
}

func subscribeToSimStream(simClient *sim.Client, streamRate armv1.StreamRate) tea.Cmd {
	return func() tea.Msg {
		frames, err := simClient.Subscribe(streamRate)
		if err != nil {
			return subscribedMsg{err: err}
		}
		return subscribedMsg{ch: frames}
	}
}

func submitControlMode(c *sim.Client, mode armv1.ControlMode) tea.Cmd {
	return func() tea.Msg {
		c.SubmitMode(mode)
		return nil
	}
}

func submitControlTarget(c *sim.Client, target *armv1.SetTargetRequest) tea.Cmd {
	return func() tea.Msg {
		c.SubmitTarget(target)
		return nil
	}
}

func submitPoseReset(c *sim.Client) tea.Cmd {
	return func() tea.Msg {
		c.SubmitReset()
		return nil
	}
}

func waitForSimFrame(frames <-chan sim.Frame) tea.Cmd {
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

func waitForCommandResult(results <-chan sim.CommandResult) tea.Cmd {
	return func() tea.Msg {
		result, ok := <-results
		if !ok {
			return disconnectMsg{err: errors.New("sim relay client closed unexpectedly")}
		}

		return commandResultMsg{result: result}
	}
}
