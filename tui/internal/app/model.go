package app

import (
	"time"

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

type confirmation int

const (
	confirmNone confirmation = iota
	confirmQuit
	confirmReset
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
	streamRate      armv1.StreamRate
	sim             *sim.Client
	addressSource   string
	lifecycle       lifecycle
	pendingConfirm  confirmation
	confirmDeadline time.Time
	activePage      page
	controlPage     controlPage
	termHeight      int
	termWidth       int
	frames          <-chan sim.Frame
	descriptor      *armv1.ModelDescriptor
	armState        *armv1.ArmState
	latestResult    *sim.CommandResult
	err             error
}

func New(client *sim.Client, streamRate armv1.StreamRate, addressSource string) tea.Model {
	return model{
		sim:             client,
		streamRate:      streamRate,
		addressSource:   addressSource,
		lifecycle:       stateConnecting,
		pendingConfirm:  confirmNone,
		confirmDeadline: time.Time{},
		activePage:      pageMonitor,
	}
}
