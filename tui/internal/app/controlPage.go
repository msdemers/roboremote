package app

import (
	tea "charm.land/bubbletea/v2"
)

type controlPage struct {
}

func (m model) updateControlPage(msg tea.KeyPressMsg) (model, tea.Cmd) {
	return m, nil
}

func (m model) viewControlPage() string {
	return "control page coming soon!"
}
