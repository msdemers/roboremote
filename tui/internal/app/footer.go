package app

import (
	"fmt"

	"charm.land/lipgloss/v2"
	"google.golang.org/grpc/status"
)

type footerData struct {
	latestCommandName string
	latestCommandErr  error
	width             int
}

var (
	successStyle    = lipgloss.NewStyle().Foreground(lipgloss.Green)
	successSymbol   = successStyle.Render("✓")
	failureStyle    = lipgloss.NewStyle().Foreground(lipgloss.Red)
	failureSymbol   = failureStyle.Render("✗")
	leftBorderStyle = lipgloss.NewStyle().Border(lipgloss.NormalBorder(), false, false, false, true).Padding(0, 1)
)

func footerBox(fd footerData) string {
	globalLegend := leftBorderStyle.Render("q (quit) · tab (next page)")

	var resultSymbol, resultMessage string
	if fd.latestCommandErr == nil {
		resultSymbol = successSymbol
		resultMessage = "Success"
	} else {
		stat := status.Convert(fd.latestCommandErr)
		resultSymbol = failureSymbol
		resultMessage = stat.Code().String() + " - " + stat.Message()
	}

	statusLine := fmt.Sprintf("%s %s: %s", resultSymbol, fd.latestCommandName, resultMessage)

	return lipgloss.JoinHorizontal(
		lipgloss.Top,
		globalLegend,
		leftBorderStyle.Width(fd.width-lipgloss.Width(globalLegend)).Render(statusLine),
	)
}
