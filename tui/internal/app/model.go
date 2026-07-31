package app

import (
	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	sim "github.com/msdemers/roboremote/tui/internal/simclient"
)

type lifecycle int

const (
	stateConnecting lifecycle = iota
	stateStreaming
	stateDisconnected
)

type page int

const (
	pageMonitor page = iota
	pageControl
)

var pageTypeToLabel = map[page]string{
	pageMonitor: "Monitor",
	pageControl: "Control",
}

var pageOrder = []page{pageMonitor, pageControl}

type model struct {
	address      string
	streamRate   armv1.StreamRate
	sim          *sim.Client
	lifecycle    lifecycle
	activePage   page
	controlPage  controlPage
	termWidth    int
	frames       <-chan sim.Frame
	descriptor   *armv1.ModelDescriptor
	armState     *armv1.ArmState
	latestResult *sim.CommandResult
	err          error
}

func New(client *sim.Client, streamRate armv1.StreamRate) tea.Model {
	return model{
		sim:        client,
		streamRate: streamRate,
		lifecycle:  stateConnecting,
		activePage: pageMonitor,
	}
}
