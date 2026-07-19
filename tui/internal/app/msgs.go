package app

import (
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

type descriptorMsg struct {
	descriptor *armv1.ModelDescriptor
}

type armStateMsg struct {
	armState *armv1.ArmState
}

type disconnectMsg struct {
	err error
}
