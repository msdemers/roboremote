package app

import (
	tea "charm.land/bubbletea/v2"
)

func (m model) View() tea.View {
	s := "Let's connect to your remote robot!\n\n"

	s += "\nPress q to quit.\n"
	return tea.NewView(s)
}
