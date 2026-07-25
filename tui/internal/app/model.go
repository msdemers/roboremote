package app

import (
	"context"

	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"github.com/msdemers/roboremote/tui/internal/stream"
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
	ctx         context.Context // breaking go's "no context in structs" convention because model is the lifecycle owner
	address     string
	streamrate  armv1.StreamRate
	lifecycle   lifecycle
	activePage  page
	controlPage controlPage
	termWidth   int
	frames      <-chan stream.Frame
	descriptor  *armv1.ModelDescriptor
	armState    *armv1.ArmState
	err         error
}

func New(ctx context.Context, address string, streamrate armv1.StreamRate) tea.Model {
	return model{
		ctx:        ctx,
		address:    address,
		streamrate: streamrate,
		lifecycle:  stateConnecting,
		activePage: pageMonitor,
	}
}
