package app

import (
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"github.com/msdemers/roboremote/tui/internal/stream"
)

type connectedMsg struct {
	ch  <-chan stream.Frame
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
