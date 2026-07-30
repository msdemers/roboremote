package app

import (
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	sim "github.com/msdemers/roboremote/tui/internal/simclient"
)

type connectedMsg struct {
	sim *sim.Client
	err error
}

type subscribedMsg struct {
	ch  <-chan sim.Frame
	err error
}

type descriptorMsg struct {
	descriptor *armv1.ModelDescriptor
}

type armStateMsg struct {
	armState *armv1.ArmState
}

type disconnectMsg struct {
	err error
}
