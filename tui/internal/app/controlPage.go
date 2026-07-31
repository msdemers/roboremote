package app

import (
	"fmt"
	"strconv"
	"strings"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

var (
	titleStyle   = lipgloss.NewStyle().Bold(true).Underline(true)
	columnStyle  = lipgloss.NewStyle().Align(lipgloss.Center).Padding(0, 1).Border(lipgloss.NormalBorder(), false, false, false, true)
	dividerStyle = lipgloss.NewStyle().Padding(0, 1)
	divider      = dividerStyle.Render("│")

	standardStyle     = lipgloss.NewStyle()
	inactiveModeStyle = standardStyle.Faint(true)
	activeModeStyle   = standardStyle.Bold(true)
	selectedStyle     = activeModeStyle
	markerString      = "❯"
	modeMarkerStyle   = lipgloss.NewStyle().Bold(true)
)

type controlPage struct {
	selected    int
	nSelectable int
}

type controlDomain int

const (
	DomainNone controlDomain = iota
	DomainTask
	DomainJoint
)

func selectionDomain(mode armv1.ControlMode) controlDomain {
	switch mode {
	case armv1.ControlMode_CONTROL_MODE_JOINT_PD_COMPENSATED, armv1.ControlMode_CONTROL_MODE_JOINT_PD_RAW:
		return DomainJoint
	case armv1.ControlMode_CONTROL_MODE_TASK_PD_COMPENSATED, armv1.ControlMode_CONTROL_MODE_TASK_PD_RAW:
		return DomainTask
	default:
		return DomainNone
	}
}

func (m model) updateControlPage(msg tea.KeyPressMsg) (model, tea.Cmd) {
	keyStr := msg.String()
	switch {
	case keyStr == "up" || keyStr == "k":
		m.controlPage.selected--
	case keyStr == "down" || keyStr == "j":
		m.controlPage.selected++
	case keyStr >= "1" && keyStr <= "9":
		digit, _ := strconv.Atoi(keyStr)
		if _, ok := armv1.ControlMode_name[int32(digit)]; ok {
			mode := armv1.ControlMode(int32(digit))
			return m, submitControlMode(m.sim, mode)
		}
	}

	if nTarget := m.controlPage.nSelectable; nTarget != 0 {
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
		controlsPane = standardStyle.Render("│ No target parameters for this controller")
	}

	mainBody := lipgloss.JoinHorizontal(lipgloss.Top, modePane, controlsPane)
	divider := standardStyle.Faint(true).Render(strings.Repeat("─", m.termWidth-2))
	compactSnapshot := m.renderCompactSnapshot()
	return lipgloss.JoinVertical(
		lipgloss.Left,
		mainBody,
		divider,
		compactSnapshot)
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

	labelsCol := lipgloss.JoinVertical(lipgloss.Left, m.jointLabelPerQIndex()...)
	labelsCol = columnStyle.Render(lipgloss.JoinVertical(lipgloss.Center, titleStyle.Render("Coordinate"), labelsCol))

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
		actualCol = append(actualCol, standardStyle.Render(fmt.Sprintf("%.2f", actualQ[i])))
		errorCol = append(errorCol, standardStyle.Render(fmt.Sprintf("%.2f", qErr)))
	}

	return lipgloss.JoinHorizontal(
		lipgloss.Top, " ",
		labelsCol,
		columnStyle.Render(lipgloss.JoinVertical(lipgloss.Center, targetCol...)),
		columnStyle.Render(lipgloss.JoinVertical(lipgloss.Center, actualCol...)),
		columnStyle.Render(lipgloss.JoinVertical(lipgloss.Center, errorCol...)),
	)
}

func (m model) jointLabelPerQIndex() []string {
	joints := m.descriptor.GetJoints()
	labels := make([]string, m.descriptor.GetNq())

	for _, j := range joints {
		firstIndex := j.GetIdxQ()
		prefix := "  "
		labelStyle := standardStyle
		if firstIndex == uint32(m.controlPage.selected) {
			labelStyle = selectedStyle
			prefix = markerString + " "
		}
		labels[firstIndex] = labelStyle.Render(prefix + j.GetName())
	}
	return labels
}

func (m model) renderTaskControlPane() string {
	targetPose := m.armState.GetCartesianTarget()
	labels, targetAsSlice := cartesianPoseToSlices(targetPose)

	styledLabels := make([]string, len(labels))
	targets := make([]string, len(targetAsSlice))

	for i, val := range targetAsSlice {
		prefix := "  "
		rowStyle := standardStyle
		if i > 2 {
			// faint style for all but the 3 translation elements
			rowStyle = rowStyle.Faint(true)
		}
		if i == m.controlPage.selected {
			rowStyle = selectedStyle
			prefix = markerString + " "
		}
		styledLabels[i] = rowStyle.Render(prefix + labels[i])
		targets[i] = rowStyle.Render(fmt.Sprintf("%.3f", val))
	}

	labelsCol := lipgloss.JoinVertical(lipgloss.Left, styledLabels...)
	labelsCol = lipgloss.JoinVertical(lipgloss.Center, titleStyle.Render("SE(3)"), labelsCol)
	targetsCol := lipgloss.JoinVertical(lipgloss.Right, targets...)
	targetsCol = lipgloss.JoinVertical(lipgloss.Right, titleStyle.Render("Desired"), targetsCol)

	_, actualAsSlice := cartesianPoseToSlices(m.armState.EndEffector)
	actuals := make([]string, len(actualAsSlice))
	diffs := make([]string, len(actualAsSlice))

	for i, val := range actualAsSlice {
		rowStyle := standardStyle
		if i > 2 {
			rowStyle = rowStyle.Faint(true)
			diffs[i] = rowStyle.Render("—.——")
		} else {
			// TODO: more rigorous handling of SE3/Quaternion diffs and errors
			diffs[i] = rowStyle.Render(fmt.Sprintf("%.3f", val-targetAsSlice[i]))
		}
		actuals[i] = rowStyle.Render(fmt.Sprintf("%.3f", val))

	}
	actualsCol := lipgloss.JoinVertical(lipgloss.Right, actuals...)
	actualsCol = lipgloss.JoinVertical(lipgloss.Right, titleStyle.Render("Actual"), actualsCol)
	diffsCol := lipgloss.JoinVertical(lipgloss.Right, diffs...)
	diffsCol = lipgloss.JoinVertical(lipgloss.Right, titleStyle.Render("Diff"), diffsCol)

	fixedColStyle := columnStyle.Width(10)
	return lipgloss.JoinHorizontal(
		lipgloss.Top, " ",
		columnStyle.Render(labelsCol),
		fixedColStyle.Render(targetsCol),
		fixedColStyle.Render(actualsCol),
		fixedColStyle.Render(diffsCol),
	)
}

func cartesianPoseToSlices(cp *armv1.CartesianPose) ([]string, []float64) {
	// scalar last ordering convention
	labels := []string{"px", "py", "pz", "qx", "qy", "qz", "qw"}
	vals := []float64{
		cp.GetX(),
		cp.GetY(),
		cp.GetZ(),
		cp.GetQx(),
		cp.GetQy(),
		cp.GetQz(),
		cp.GetQw(),
	}
	return labels, vals
}

func formatFloatsToStrings[T float32 | float64](slice []T, sFormat string) []string {
	result := make([]string, len(slice))

	for i, val := range slice {
		result[i] = fmt.Sprintf(sFormat, val)
	}
	return result
}

func (m model) renderCompactSnapshot() string {
	style := standardStyle.Faint(true)

	qSnippet := "q: " + strings.Join(
		formatFloatsToStrings(m.armState.GetQ().GetQ(), "%.2f"),
		", ",
	)

	vSnippet := "v: " + strings.Join(
		formatFloatsToStrings(m.armState.GetV().GetV(), "%.2f"),
		", ",
	)

	tauSnippet := "τ: " + strings.Join(
		formatFloatsToStrings(m.armState.GetTau().GetTau(), "%.2f"),
		", ",
	)

	dofWidget := lipgloss.JoinVertical(
		lipgloss.Left,
		style.Render(qSnippet),
		style.Render(vSnippet),
		style.Render(tauSnippet),
	)

	eePose := m.armState.GetEndEffector()
	pSnippet := fmt.Sprintf("pos: %.3f, %.3f, %.3f", eePose.GetX(), eePose.GetY(), eePose.GetZ())
	quatSnippet := fmt.Sprintf("quat: %.2f, %.2f, %.2f, %.2f\n  ↳(x,y,z,w)", eePose.GetQx(), eePose.GetQy(), eePose.GetQz(), eePose.GetQw())

	eeWidget := lipgloss.JoinVertical(
		lipgloss.Left,
		style.Render(pSnippet),
		style.Render(quatSnippet),
	)

	return lipgloss.JoinHorizontal(lipgloss.Top, dofWidget, "   ", eeWidget)
}
