package app

import (
	"fmt"

	tea "charm.land/bubbletea/v2"
)

func (m model) View() tea.View {
	s := "::ROBOREMOTE::\n\n"

	switch m.lifecycle {
	case stateConnecting:
		s += "connecting...\n"
	case stateStreaming:
		if m.armState == nil {
			s += "waiting for first simulation frame..."
		} else {
			s += fmt.Sprintf("t = %8.2f s\n", m.armState.GetSimTime())
		}
	case stateDisconnected:
		s += fmt.Sprintf("disconnected: %v", m.err)
	}

	s += "\nPress q to quit.\n"
	return tea.NewView(s)
}
