package app

import (
	"errors"

	tea "charm.land/bubbletea/v2"
)

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "tab":
			switch m.activePage {
			case pageMonitor:
				m.activePage = pageControl
				return m, nil
			case pageControl:
				m.activePage = pageMonitor
				return m, nil
			}
		}
		// not a global navigation KeyPress. Delegate to per-page handlers
		switch m.activePage {
		case pageControl:
			return m.updateControlPage(msg)
		}
	case tea.WindowSizeMsg:
		m.termWidth = msg.Width
		return m, nil
	case subscribedMsg:
		if msg.err != nil {
			m.lifecycle = stateDisconnected
			m.err = msg.err
			return m, nil
		}
		m.frames = msg.ch
		return m, waitForSimFrame(m.frames)
	case descriptorMsg:
		if err := validateDescriptor(msg.descriptor); err != nil {
			m.err = err
			m.lifecycle = stateDisconnected
			return m, nil
		}
		m.descriptor = msg.descriptor
		m.lifecycle = stateStreaming
		return m, waitForSimFrame(m.frames)
	case armStateMsg:
		if m.lifecycle != stateStreaming {
			m.lifecycle = stateDisconnected
			m.err = errors.New("received ArmState when expecting a ModelDescriptor")
			m.frames = nil
			return m, nil
		}
		if err := validateFrameShape(m.descriptor, msg.armState); err != nil {
			m.err = err
			m.lifecycle = stateDisconnected
			return m, nil
		}

		// update controlPage parameters and caches
		oldDomain := selectionDomain(m.armState.GetActiveMode())
		if oldDomain != selectionDomain(msg.armState.GetActiveMode()) {
			m.controlPage.selected = 0
		}
		m.armState = msg.armState
		return m, waitForSimFrame(m.frames)
	case disconnectMsg:
		m.lifecycle = stateDisconnected
		m.err = msg.err
		m.frames = nil
		m.descriptor = nil
		m.armState = nil
		return m, nil
	}

	return m, nil
}
