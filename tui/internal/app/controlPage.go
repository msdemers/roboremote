package app

import (
	"fmt"
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

var (
	titleStyle        = lipgloss.NewStyle().Bold(true).Underline(true)
	standardStyle     = lipgloss.NewStyle()
	inactiveModeStyle = standardStyle.Faint(true)
	activeModeStyle   = standardStyle.Bold(true)
	selectedStyle     = activeModeStyle
	markerString      = "❯"
	modeMarkerStyle   = lipgloss.NewStyle().Bold(true)
)

type controlPage struct {
	selected int
}

func (m model) updateControlPage(msg tea.KeyPressMsg) (model, tea.Cmd) {
	// determine the length of the controller command target
	targetInterface := m.armState.GetActiveTarget()
	var nTarget int
	switch target := targetInterface.(type) {
	case *armv1.ArmState_JointTarget:
		nTarget = len(target.JointTarget.GetQ())
	case *armv1.ArmState_CartesianTarget:
		nTarget = 3 // only allow selection and editing of the x,y,z positions
	default:
		nTarget = 0
	}

	switch msg.String() {
	case "up", "k":
		m.controlPage.selected--
	case "down", "j":
		m.controlPage.selected++
	}

	if nTarget != 0 {
		m.controlPage.selected = (m.controlPage.selected + nTarget) % nTarget
	} else {
		m.controlPage.selected = 0
	}

	return m, nil
}

func (m model) viewControlPage() string {
	modePane := m.renderControlModeList()
	var controlsPane string
	switch m.armState.GetActiveMode() {
	case armv1.ControlMode_CONTROL_MODE_JOINT_PD_RAW, armv1.ControlMode_CONTROL_MODE_JOINT_PD_COMPENSATED:
		controlsPane = m.renderJointControlPane()
	case armv1.ControlMode_CONTROL_MODE_TASK_PD_RAW, armv1.ControlMode_CONTROL_MODE_TASK_PD_COMPENSATED:
		controlsPane = m.renderTaskControlPane()
	default:
		controlsPane = standardStyle.Render("No target settings for this controller")
	}

	return lipgloss.JoinHorizontal(lipgloss.Top, modePane, controlsPane)
}

func (m model) renderControlModeList() string {
	activeMode := m.armState.GetActiveMode()
	modeVals := armv1.ControlMode(0).Descriptor().Values()
	modesSlice := make([]string, 0, modeVals.Len())

	for i := 0; i < modeVals.Len(); i++ {
		mv := modeVals.Get(i)
		mode := armv1.ControlMode(mv.Number())
		if mode == armv1.ControlMode_CONTROL_MODE_UNSPECIFIED {
			continue // skip the unset case
		}
		prefix := fmt.Sprintf("%d: ", mv.Number())
		modeName := strings.TrimPrefix(string(mv.Name()), "CONTROL_MODE_")
		if mode == activeMode {
			modesSlice = append(modesSlice, fmt.Sprintf("%s %s", modeMarkerStyle.Render(markerString), activeModeStyle.Render(prefix+modeName)))
		} else {
			modesSlice = append(modesSlice, fmt.Sprintf("  %s", inactiveModeStyle.Render(prefix+modeName)))
		}
	}
	// create a default line for any unkown control modes
	unkownModeLabel := " : UNKNOWN_MODE"
	_, known := armv1.ControlMode_name[int32(activeMode)]
	if known {
		modesSlice = append(modesSlice, fmt.Sprintf("  %s", inactiveModeStyle.Render("—: ————")))
	} else {
		modesSlice = append(modesSlice, fmt.Sprintf("%s %s(%d)", modeMarkerStyle.Render(markerString), activeModeStyle.Render(unkownModeLabel), int(activeMode.Number())))
	}

	return lipgloss.JoinVertical(lipgloss.Left, modesSlice...)
}

func (m model) renderJointControlPane() string {
	targetQ := m.armState.GetJointTarget().GetQ()
	actualQ := m.armState.GetQ().GetQ()
	nQ := len(targetQ)

	targetCol := make([]string, 0, nQ+1)
	actualCol := make([]string, 0, nQ+1)
	errorCol := make([]string, 0, nQ+1)
	targetCol = append(targetCol, titleStyle.Render("Q Desired"))
	actualCol = append(actualCol, titleStyle.Render("Q Actual"))
	errorCol = append(errorCol, titleStyle.Render("Q Error"))

	for i := 0; i < nQ; i++ {
		qErr := actualQ[i] - targetQ[i]

		var controlStyle lipgloss.Style
		if i == m.controlPage.selected {
			controlStyle = selectedStyle
		} else {
			controlStyle = standardStyle
		}
		targetCol = append(targetCol, controlStyle.Render(fmt.Sprintf("%.2f", targetQ[i])))
		actualCol = append(actualCol, controlStyle.Render(fmt.Sprintf("%.2f", actualQ[i])))
		errorCol = append(errorCol, controlStyle.Render(fmt.Sprintf("%.2f", qErr)))
	}

	return lipgloss.JoinHorizontal(
		lipgloss.Top, "    ",
		lipgloss.JoinVertical(lipgloss.Center, targetCol...), " ",
		lipgloss.JoinVertical(lipgloss.Center, actualCol...), " ",
		lipgloss.JoinVertical(lipgloss.Center, errorCol...), " ",
	)
}

func (m model) renderTaskControlPane() string {
	return standardStyle.Render("Task Space Control coming soon!")
}
