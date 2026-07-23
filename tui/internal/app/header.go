package app

import (
	"fmt"

	"charm.land/lipgloss/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

func streamRateLabel(rate armv1.StreamRate) string {
	switch rate {
	case armv1.StreamRate_STREAM_RATE_30:
		return "30 Hz"
	case armv1.StreamRate_STREAM_RATE_60:
		return "60 Hz"
	case armv1.StreamRate_STREAM_RATE_120:
		return "120 Hz"
	default:
		return "60 Hz (default)"
	}
}

func connectingBadge() string {
	return lipgloss.NewStyle().Foreground(lipgloss.Color("3")).Render("CONNECTING")
}

func streamingBadge(rate armv1.StreamRate, state *armv1.ArmState) string {
	return lipgloss.NewStyle().Foreground(lipgloss.Color("10")).Render(
		fmt.Sprintf("STREAMING | %s | t = %.2f s", streamRateLabel(rate), state.GetSimTime()),
	)
}

func disconnectedBadge(err error) string {
	return lipgloss.NewStyle().Foreground(lipgloss.Color("1")).Render(
		fmt.Sprintf("DISCONNECTED: %v", err))
}

type headerData struct {
	lifecycle  lifecycle
	address    string
	descriptor *armv1.ModelDescriptor
	streamRate armv1.StreamRate
	armState   *armv1.ArmState
	err        error
	termWidth  int
}

func headerBox(hd headerData) string {
	title := "RoboRemote"
	statusBadge := ""

	switch hd.lifecycle {
	case stateConnecting:
		statusBadge += connectingBadge()
	case stateStreaming:
		statusBadge += streamingBadge(hd.streamRate, hd.armState)
	case stateDisconnected:
		statusBadge += disconnectedBadge(hd.err)
	}

	line1 := lipgloss.JoinHorizontal(lipgloss.Center, title, " | ", hd.address, " | ", hd.descriptor.GetModelName())
	line1 = lipgloss.NewStyle().Bold(true).Render(line1)
	line2 := statusBadge
	headerContent := lipgloss.JoinVertical(lipgloss.Left, line1, line2)

	return lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).Width(hd.termWidth).Render(headerContent)
}
