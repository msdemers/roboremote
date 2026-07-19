package app

import (
	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

type lifecycle int

const (
	stateConnecting lifecycle = iota
	stateAwaitingDescriptor
	stateStreaming
	stateDisconnected
)

type model struct {
	lifecycle  lifecycle
	descriptor *armv1.ModelDescriptor
	armState   *armv1.ArmState
	err        error
}

func New() tea.Model {
	return model{
		lifecycle: stateConnecting,
	}
}
