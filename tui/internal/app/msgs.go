package app

import (
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	sim "github.com/msdemers/roboremote/tui/internal/simclient"
)

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

type commandResultMsg struct {
	result sim.CommandResult
}

type disconnectMsg struct {
	err error
}
