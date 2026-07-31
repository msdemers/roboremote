package app

import (
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
)

var (

	// Inactive tabs are bounded on top, left, and right, but closed on the bottom.
	inactiveBorder = lipgloss.Border{
		Top:         "─",
		Bottom:      "─",
		Left:        "│",
		Right:       "│",
		TopLeft:     "╭",
		TopRight:    "╮",
		BottomLeft:  "┴",
		BottomRight: "┴",
	}
	inactiveTabStyle = lipgloss.NewStyle().
				Border(inactiveBorder).
				Padding(0, 2)

	// Active tabs remove the bottom border so they seamlessly "open into" the content window box below them.
	activeBorder = lipgloss.Border{
		Top:         "─",
		Bottom:      " ",
		Left:        "│",
		Right:       "│",
		TopLeft:     "╭",
		TopRight:    "╮",
		BottomLeft:  "┘",
		BottomRight: "└",
	}
	activeTabStyle = lipgloss.NewStyle().
			Border(activeBorder).
			Bold(true).
			Padding(0, 2)

	contentBoxStyle = lipgloss.NewStyle().
			Padding(0, 0).
			Border(lipgloss.RoundedBorder(), false, true, true, true) // No top border!
)

func (m model) viewTabBar() string {
	var renderedTabs []string

	for i, pageType := range pageOrder {
		isFirst, isLast, isActive := i == 0, i == len(pageOrder)-1, pageType == m.activePage

		label := pageTypeToLabel[pageType]
		var style lipgloss.Style
		if isActive {
			style = activeTabStyle
		} else {
			style = inactiveTabStyle
		}

		border, _, _, _, _ := style.GetBorder()
		if isFirst && isActive {
			border.BottomLeft = "│"
		} else if isFirst && !isActive {
			border.BottomLeft = "├"
		} else if isLast && isActive {
			//border.BottomRight = "│"
		} else if isLast && !isActive {
			//border.BottomRight = "┤"
		}
		style = style.Border(border)
		renderedTabs = append(renderedTabs, style.Render(label))
	}

	row := lipgloss.JoinHorizontal(lipgloss.Bottom, renderedTabs...)
	if m.termWidth > 0 {
		spacesRemaining := m.termWidth - lipgloss.Width(row)
		row += strings.Repeat("─", spacesRemaining-1) + "╮"
	}

	return row
}

func (m model) View() tea.View {
	s := ""

	s += headerBox(headerData{
		lifecycle:  m.lifecycle,
		address:    m.address,
		descriptor: m.descriptor,
		streamRate: m.streamRate,
		armState:   m.armState,
		err:        m.err,
		termWidth:  m.termWidth,
	}) + "\n"

	s += m.viewTabBar() + "\n"

	switch m.lifecycle {
	case stateConnecting:
		s += ""
	case stateStreaming:
		pageStyle := contentBoxStyle.Width(m.termWidth)
		if m.armState == nil {
			s += pageStyle.Render("waiting for first simulation frame...")
		} else {
			switch m.activePage {
			case pageMonitor:
				s += pageStyle.Render(m.viewMonitorPage())
			case pageControl:
				s += pageStyle.Render(m.viewControlPage())
			}

		}
	case stateDisconnected:
		s += ""
	}

	s += "\n"

	fd := footerData{width: m.termWidth}

	if m.latestResult != nil {
		fd.latestCommandName = m.latestResult.Kind.String()
		fd.latestCommandErr = m.latestResult.Err
	}
	s += footerBox(fd)

	v := tea.NewView(s)
	v.AltScreen = true
	return v
}
