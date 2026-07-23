package app

import (
	"fmt"

	"charm.land/bubbles/v2/table"
	tea "charm.land/bubbletea/v2"
)

func (m model) View() tea.View {
	s := ""

	s += headerBox(headerData{
		lifecycle:  m.lifecycle,
		address:    m.address,
		descriptor: m.descriptor,
		streamRate: m.streamrate,
		armState:   m.armState,
		err:        m.err,
		termWidth:  m.termWidth,
	})

	switch m.lifecycle {
	case stateConnecting:
		s += ""
	case stateStreaming:
		if m.armState == nil {
			s += "waiting for first simulation frame..."
		} else {
			s += fmt.Sprintf("t = %8.2f s\n", m.armState.GetSimTime())

			rows := toTableRows(jointRows(m.descriptor, m.armState))
			jt := table.New(
				table.WithColumns(tableColumns()),
				table.WithWidth(tableWidth(tableColumns())),
				table.WithHeight(len(rows)+1),
				table.WithRows(rows),
			)
			s += jt.View()
		}
	case stateDisconnected:
		s += ""
	}

	s += "\n\nPress q to quit.\n"

	v := tea.NewView(s)
	v.AltScreen = true
	return v
}
