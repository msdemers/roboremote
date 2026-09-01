package app

import (
	"math"
	"slices"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
)

func key(s string) tea.KeyPressMsg {
	return tea.KeyPressMsg{Text: s}
}

func checkCommand(t *testing.T, gotCmd tea.Cmd, wantCmdRegime cmdRegime) {
	switch wantCmdRegime {
	case cmdNone:
		if gotCmd != nil {
			t.Errorf("Update() returned a cmd when nil expected")
		}
	case cmdQuit:
		msg := gotCmd()
		if _, ok := msg.(tea.QuitMsg); !ok {
			t.Errorf("Update() returned %T, expected %T", msg, tea.QuitMsg{})
		}
	case cmdOpaque:
		if gotCmd == nil {
			t.Errorf("Update() returned nil cmd, expected non nil")
		}
	}
}

type cmdRegime int

const (
	cmdNone cmdRegime = iota
	cmdQuit
	cmdOpaque
)

func TestUpdate_GlobalKeyRouting(t *testing.T) {
	tests := []struct {
		name            string
		seed            model
		key             tea.KeyPressMsg
		wantPage        page
		wantConfirm     confirmation
		wantCmd         cmdRegime
		wantNewDeadline bool
	}{
		{
			name:            "tab from monitor selects control",
			seed:            model{activePage: pageMonitor},
			key:             tea.KeyPressMsg{Code: tea.KeyTab},
			wantPage:        pageControl,
			wantConfirm:     confirmNone,
			wantCmd:         cmdNone,
			wantNewDeadline: false,
		},
		{
			name:            "tab from control selects monitor",
			seed:            model{activePage: pageControl},
			key:             tea.KeyPressMsg{Code: tea.KeyTab},
			wantPage:        pageMonitor,
			wantConfirm:     confirmNone,
			wantCmd:         cmdNone,
			wantNewDeadline: false,
		},
		{
			name:            "q from Monitor arms quit confirm",
			seed:            model{activePage: pageMonitor, pendingConfirm: confirmNone},
			key:             key("q"),
			wantPage:        pageMonitor,
			wantConfirm:     confirmQuit,
			wantCmd:         cmdOpaque,
			wantNewDeadline: true,
		},
		{
			name:            "q from Control arms quit confirm",
			seed:            model{activePage: pageControl, pendingConfirm: confirmNone},
			key:             key("q"),
			wantPage:        pageControl,
			wantConfirm:     confirmQuit,
			wantCmd:         cmdOpaque,
			wantNewDeadline: true,
		},
		{
			name:            "ctrl+c from Monitor quits immediately",
			seed:            model{activePage: pageMonitor, pendingConfirm: confirmNone},
			key:             key("ctrl+c"),
			wantPage:        pageMonitor,
			wantConfirm:     confirmNone,
			wantCmd:         cmdQuit,
			wantNewDeadline: false,
		},
		{
			name:            "ctrl+c from Control quits immediately",
			seed:            model{activePage: pageControl, pendingConfirm: confirmNone},
			key:             key("ctrl+c"),
			wantPage:        pageControl,
			wantConfirm:     confirmNone,
			wantCmd:         cmdQuit,
			wantNewDeadline: false,
		},
		{
			name:            "ctrl+c while pendingConfirm quits immediately",
			seed:            model{activePage: pageControl, pendingConfirm: confirmQuit},
			key:             key("ctrl+c"),
			wantPage:        pageControl,
			wantConfirm:     confirmQuit,
			wantCmd:         cmdQuit,
			wantNewDeadline: false,
		},
		{
			name:            "confirmQuit - y quits immediately",
			seed:            model{activePage: pageMonitor, pendingConfirm: confirmQuit},
			key:             key("y"),
			wantPage:        pageMonitor,
			wantConfirm:     confirmNone,
			wantCmd:         cmdQuit,
			wantNewDeadline: false,
		},
		{
			name:            "confirmQuit - n cancels quit",
			seed:            model{activePage: pageMonitor, pendingConfirm: confirmQuit},
			key:             key("n"),
			wantPage:        pageMonitor,
			wantConfirm:     confirmNone,
			wantCmd:         cmdNone,
			wantNewDeadline: false,
		},
		{
			name:            "confirmQuit - esc cancels quit",
			seed:            model{activePage: pageMonitor, pendingConfirm: confirmQuit, confirmDeadline: time.Now().Add(time.Minute)},
			key:             tea.KeyPressMsg{Code: tea.KeyEsc},
			wantPage:        pageMonitor,
			wantConfirm:     confirmNone,
			wantCmd:         cmdNone,
			wantNewDeadline: false,
		},
		{
			name:            "confirmQuit - tab gets swallowed",
			seed:            model{activePage: pageMonitor, pendingConfirm: confirmQuit},
			key:             tea.KeyPressMsg{Code: tea.KeyTab},
			wantPage:        pageMonitor,
			wantConfirm:     confirmQuit,
			wantCmd:         cmdNone,
			wantNewDeadline: false,
		},
		{
			name:            "confirmReset - y confirms and returns a cmd",
			seed:            model{activePage: pageControl, pendingConfirm: confirmReset, confirmDeadline: time.Now().Add(time.Minute)},
			key:             key("y"),
			wantPage:        pageControl,
			wantConfirm:     confirmNone,
			wantCmd:         cmdOpaque,
			wantNewDeadline: false,
		},
		{
			name:            "confirmReset - + gets swallowed",
			seed:            model{activePage: pageControl, pendingConfirm: confirmReset, confirmDeadline: time.Now().Add(time.Minute)},
			key:             key("+"),
			wantPage:        pageControl,
			wantConfirm:     confirmReset,
			wantCmd:         cmdNone,
			wantNewDeadline: false,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			before := time.Now()
			next, cmd := tc.seed.Update(tc.key)
			after := time.Now()
			got, ok := next.(model)

			if !ok {
				t.Fatalf("Update() = %T, want model", next)
			}

			if got.activePage != tc.wantPage {
				t.Errorf("activePage = %v, want %v", got.activePage, tc.wantPage)
			}

			if got.pendingConfirm != tc.wantConfirm {
				t.Errorf("pendingConfirm = %v, want %v", got.pendingConfirm, tc.wantConfirm)
			}

			checkCommand(t, cmd, tc.wantCmd)

			if tc.wantNewDeadline {
				if got.confirmDeadline.IsZero() || got.confirmDeadline.Before(before.Add(confirmationTimeout)) {
					t.Errorf("confirmDeadline = %v, want > %v", got.confirmDeadline, before)
				}
				if got.confirmDeadline.After(after.Add(confirmationTimeout)) {
					t.Errorf("confirmDeadline = %v, want < %v", got.confirmDeadline, after.Add(confirmationTimeout))
				}
			} else {
				if !got.confirmDeadline.Equal(tc.seed.confirmDeadline) {
					t.Errorf("confirmDeadline = %v, want %v", got.confirmDeadline, tc.seed.confirmDeadline)
				}
			}

		})
	}
}

func TestUpdateControlPage_Selection(t *testing.T) {
	tests := []struct {
		name         string
		seed         model
		key          tea.KeyPressMsg
		wantSelected int
		wantCmd      cmdRegime
	}{
		{
			name: "j increments selected",
			seed: model{
				controlPage: controlPage{
					selectionDomain: DomainTask,
					selected:        1, nSelectable: 3,
				},
			},
			key:          key("j"),
			wantSelected: 2,
			wantCmd:      cmdNone,
		},
		{
			name: "j wraps selected around nSelectable",
			seed: model{
				controlPage: controlPage{
					selectionDomain: DomainTask,
					selected:        2, nSelectable: 3,
				},
			},
			key:          key("j"),
			wantSelected: 0,
			wantCmd:      cmdNone,
		},
		{
			name: "k decrements selected",
			seed: model{
				controlPage: controlPage{
					selectionDomain: DomainTask,
					selected:        1, nSelectable: 3,
				},
			},
			key:          key("k"),
			wantSelected: 0,
			wantCmd:      cmdNone,
		},
		{
			name: "k wraps selected around nSelectable",
			seed: model{
				controlPage: controlPage{
					selectionDomain: DomainTask,
					selected:        0, nSelectable: 3,
				},
			},
			key:          key("k"),
			wantSelected: 2,
			wantCmd:      cmdNone,
		},
		{
			name: "down increments selected",
			seed: model{
				controlPage: controlPage{
					selectionDomain: DomainTask,
					selected:        1, nSelectable: 3,
				},
			},
			key:          tea.KeyPressMsg{Code: tea.KeyDown},
			wantSelected: 2,
			wantCmd:      cmdNone,
		},
		{
			name: "j mutates nothing when nSelectable is zero",
			seed: model{
				controlPage: controlPage{
					selectionDomain: DomainNone,
					selected:        0, nSelectable: 0,
				},
			},
			key:          key("j"),
			wantSelected: 0,
			wantCmd:      cmdNone,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			next, cmd := tc.seed.updateControlPage(tc.key)

			got := next.controlPage

			if got.selectionDomain != tc.seed.controlPage.selectionDomain {
				t.Errorf("selectionDomain = %v, want %v", got.selectionDomain, tc.seed.controlPage.selectionDomain)
			}
			if got.selected != tc.wantSelected {
				t.Errorf("selected = %v, want %v", got.selected, tc.wantSelected)
			}
			checkCommand(t, cmd, tc.wantCmd)
		})
	}
}

func TestControlPage_JogCursor(t *testing.T) {
	tests := []struct {
		name               string
		seed               *controlPage
		jogSteps           int
		wantTargetCursor   []float64
		wantTouched        []bool
		wantNewLastJogTime bool
	}{
		{
			name: "jogCursor on empty target cursor gets swallowed",
			seed: &controlPage{
				selected: 0, nSelectable: 0,
			},
			jogSteps:           1,
			wantTargetCursor:   []float64{},
			wantTouched:        []bool{},
			wantNewLastJogTime: false,
		},
		{
			name: "jogCursor gets swallowed when selected is out of range",
			seed: &controlPage{
				selected: 5, nSelectable: 5,
				targetCursor: make([]float64, 5), touched: make([]bool, 5),
			},
			jogSteps:           1,
			wantTargetCursor:   make([]float64, 5),
			wantTouched:        make([]bool, 5),
			wantNewLastJogTime: false,
		},
		{
			name: "jogCursor gets swallowed when selected is negative",
			seed: &controlPage{
				selectionDomain: DomainJoint, selected: -1, nSelectable: 7,
				targetCursor: make([]float64, 7), touched: make([]bool, 7),
			},
			jogSteps:           1,
			wantTargetCursor:   make([]float64, 7),
			wantTouched:        make([]bool, 7),
			wantNewLastJogTime: false,
		},
		{
			name: "jogCursor gets swallowed when DomainNone",
			seed: &controlPage{
				selectionDomain: DomainNone, selected: 0, nSelectable: 3,
				targetCursor: make([]float64, 3), touched: make([]bool, 3),
			},
			jogSteps:           1,
			wantTargetCursor:   make([]float64, 3),
			wantTouched:        make([]bool, 3),
			wantNewLastJogTime: false,
		},
		{
			name: "jogCursor(n) under DomainJoint increments targetCursor by n angular steps",
			seed: &controlPage{
				selectionDomain: DomainJoint, selected: 1, nSelectable: 3,
				targetCursor: []float64{0.3, -0.4, 0.2}, touched: []bool{false, false, false},
			},
			jogSteps:           4,
			wantTargetCursor:   []float64{0.3, -0.4 + 4*jogStepRadians, 0.2},
			wantTouched:        []bool{false, true, false},
			wantNewLastJogTime: true,
		},
		{
			name: "jogCursor(-n) under DomainJoint decrements targetCursor by n angular steps",
			seed: &controlPage{
				selectionDomain: DomainJoint, selected: 1, nSelectable: 3,
				targetCursor: make([]float64, 3), touched: []bool{false, false, false},
			},
			jogSteps:           -4,
			wantTargetCursor:   []float64{0.0, -4 * jogStepRadians, 0.0},
			wantTouched:        []bool{false, true, false},
			wantNewLastJogTime: true,
		},
		{
			name: "jogCursor(n) under DomainTask increments targetCursor by n translational steps",
			seed: &controlPage{
				selectionDomain: DomainTask, selected: 1, nSelectable: 3,
				targetCursor: make([]float64, 3), touched: []bool{false, false, false},
			},
			jogSteps:           4,
			wantTargetCursor:   []float64{0.0, 4 * jogStepMeters, 0.0},
			wantTouched:        []bool{false, true, false},
			wantNewLastJogTime: true,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := *tc.seed
			got.targetCursor = slices.Clone(tc.seed.targetCursor)
			got.touched = slices.Clone(tc.seed.touched)

			before := time.Now()
			got.jogCursor(tc.jogSteps)
			after := time.Now()

			targetCursorsEqual := slices.EqualFunc(got.targetCursor, tc.wantTargetCursor, func(a, b float64) bool {
				return math.Abs(a-b) < 1e-9
			})
			if !targetCursorsEqual {
				t.Errorf("targetCursor = %v, want %v", got.targetCursor, tc.wantTargetCursor)
			}
			if !slices.Equal(got.touched, tc.wantTouched) {
				t.Errorf("touched = %v, want %v", got.touched, tc.wantTouched)
			}
			if got.selectionDomain != tc.seed.selectionDomain {
				t.Errorf("selectionDomain = %v, want %v", got.selectionDomain, tc.seed.selectionDomain)
			}
			if got.selected != tc.seed.selected {
				t.Errorf("selected = %v, want %v", got.selected, tc.seed.selected)
			}
			if got.nSelectable != tc.seed.nSelectable {
				t.Errorf("nSelectable = %v, want %v", got.nSelectable, tc.seed.nSelectable)
			}

			if tc.wantNewLastJogTime {
				if got.lastJogTime.Before(before) {
					t.Errorf("lastJogTime = %v, want after %v", got.lastJogTime, before)
				}
				if got.lastJogTime.After(after) {
					t.Errorf("lastJogTime = %v, want before %v", got.lastJogTime, after)
				}
			} else {
				if !got.lastJogTime.Equal(tc.seed.lastJogTime) {
					t.Errorf("lastJogTime = %v, want %v", got.lastJogTime, tc.seed.lastJogTime)
				}
			}
		})
	}
}

func TestUpdate_ConfirmationExpired(t *testing.T) {
	tests := []struct {
		name        string
		seed        model
		wantConfirm confirmation
	}{
		{
			name: "confirmation survives future deadline",
			seed: model{
				pendingConfirm:  confirmQuit,
				confirmDeadline: time.Now().Add(time.Minute),
			},
			wantConfirm: confirmQuit,
		},
		{
			name: "confirmation closes after deadline",
			seed: model{
				pendingConfirm:  confirmQuit,
				confirmDeadline: time.Now().Add(-time.Minute),
			},
			wantConfirm: confirmNone,
		},
		{
			name: "cleared confirmation stays cleared after deadline",
			seed: model{
				pendingConfirm:  confirmNone,
				confirmDeadline: time.Now().Add(-time.Minute),
			},
			wantConfirm: confirmNone,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			next, cmd := tc.seed.Update(confirmationExpiredMsg{})
			got, ok := next.(model)

			if !ok {
				t.Fatalf("Update() = %T, want model", next)
			}

			if got.pendingConfirm != tc.wantConfirm {
				t.Errorf("pendingConfirm = %v, want %v", got.pendingConfirm, tc.wantConfirm)
			}
			checkCommand(t, cmd, cmdNone)
		})
	}
}
