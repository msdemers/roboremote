package app

import (
	"errors"
	"slices"
	"time"

	tea "charm.land/bubbletea/v2"
)

const (
	jogIdleTime         = 200 * time.Millisecond
	confirmationTimeout = 3 * time.Second
)

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {

	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		// always be ready to force-quit the program
		if msg.String() == "ctrl+c" {
			return m, tea.Quit
		}

		// handle any pending confirmation
		if m.pendingConfirm != confirmNone {
			switch msg.String() {
			case "y", "Y":
				// confirm the pending command
				switch m.pendingConfirm {
				case confirmQuit:
					m.pendingConfirm = confirmNone
					return m, tea.Quit
				case confirmReset:
					m.pendingConfirm = confirmNone
					return m, submitPoseReset(m.sim)
				}
			case "n", "N", "esc":
				// cancel the pending confirmation
				m.pendingConfirm = confirmNone
				return m, nil
			}

			return m, nil
		}

		switch msg.String() {
		case "q":
			return m.openConfirm(confirmQuit)
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

	case confirmationExpiredMsg:
		if time.Now().Before(m.confirmDeadline) {
			return m, nil
		}
		m.pendingConfirm = confirmNone
		return m, nil
	case tea.WindowSizeMsg:
		m.termHeight = msg.Height
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
		newDomain := selectionDomain(msg.armState.GetActiveMode())
		if newDomain != oldDomain {
			m.controlPage.selectionDomain = newDomain
			m.controlPage.selected = 0
			m.controlPage.nSelectable = 0
			switch newDomain {
			case DomainTask:
				m.controlPage.nSelectable = 3
			case DomainJoint:
				m.controlPage.nSelectable = int(m.descriptor.GetNq())
			}
			m.controlPage.lastJogTime = time.Time{}
		}
		if time.Since(m.controlPage.lastJogTime) > jogIdleTime {
			switch newDomain {
			case DomainTask:
				target := msg.armState.GetCartesianTarget()
				m.controlPage.targetCursor = []float64{
					target.GetX(), target.GetY(), target.GetZ(), target.GetQx(), target.GetQy(), target.GetQz(), target.GetQw(),
				}

			case DomainJoint:
				target := msg.armState.GetJointTarget()
				m.controlPage.targetCursor = slices.Clone(target.GetQ())

			case DomainNone:
				m.controlPage.targetCursor = []float64{}
			}
			m.controlPage.touched = make([]bool, len(m.controlPage.targetCursor))
		}

		m.armState = msg.armState

		return m, waitForSimFrame(m.frames)
	case commandResultMsg:
		m.latestResult = &msg.result
		return m, waitForCommandResult(m.sim.Results())
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

func (m model) openConfirm(c confirmation) (model, tea.Cmd) {
	m.pendingConfirm = c
	m.confirmDeadline = time.Now().Add(confirmationTimeout)
	return m, expireConfirmation()
}
