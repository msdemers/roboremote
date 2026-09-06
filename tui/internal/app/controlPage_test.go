package app

import (
	"math"
	"slices"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

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

func TestUpdateControlPage_ModeKeys(t *testing.T) {
	tests := []struct {
		name         string
		seed         model
		key          tea.KeyPressMsg
		wantSelected int
		wantCmd      cmdRegime
	}{
		{
			name: "0 key excluded",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					nSelectable: 3, selected: 5, // this is an invalid combo
				},
			},
			key:          tea.KeyPressMsg{Text: "0"},
			wantSelected: 2,
			wantCmd:      cmdNone,
		},
		{
			name: "1 key fires command",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					nSelectable: 3, selected: 5, // this is an invalid combo
				},
			},
			key:          tea.KeyPressMsg{Text: "1"},
			wantSelected: 5,
			wantCmd:      cmdOpaque,
		},
		{
			name: "5 key fires command",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					nSelectable: 3, selected: 5, // this is an invalid combo
				},
			},
			key:          tea.KeyPressMsg{Text: "1"},
			wantSelected: 5,
			wantCmd:      cmdOpaque,
		},
		{
			name: "6 key excluded",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					nSelectable: 3, selected: 5, // this is an invalid combo
				},
			},
			key:          tea.KeyPressMsg{Text: "6"},
			wantSelected: 2,
			wantCmd:      cmdNone,
		},
	}

	for _, tc := range tests {
		next, cmd := tc.seed.Update(tc.key)
		got, ok := next.(model)
		if !ok {
			t.Fatalf("Update() = %T, want model", next)
		}

		checkCommand(t, cmd, tc.wantCmd)

		if got.controlPage.selected != tc.wantSelected {
			t.Errorf("selected = %v, wanted %v", got.controlPage.selected, tc.wantSelected)
		}
	}
}

func TestUpdateControlPage_DomainChangeResetsJogScale(t *testing.T) {
	desc := &armv1.ModelDescriptor{Nq: 3, Nv: 3}
	state := &armv1.ArmState{
		ActiveMode: armv1.ControlMode_CONTROL_MODE_JOINT_PD_COMPENSATED,
		Q:          &armv1.Coordinates{Q: make([]float64, 3)},
		V:          &armv1.Velocities{V: make([]float64, 3)},
		Tau:        &armv1.Actuation{Tau: make([]float64, 3)},
		ActiveTarget: &armv1.ArmState_JointTarget{
			JointTarget: &armv1.Coordinates{Q: make([]float64, 3)},
		},
	}

	seed := model{
		lifecycle:  stateStreaming,
		activePage: pageControl,
		controlPage: controlPage{
			nSelectable: 3, selected: 0, selectionDomain: DomainTask, jogScale: (1 + jogRampAlpha),
		},
		descriptor: desc,
	}

	next, _ := seed.Update(armStateMsg{armState: state})
	next2, _ := next.Update(tea.KeyPressMsg{Text: "+"})
	got, ok := next2.(model)
	if !ok {
		t.Fatalf("Update() = %T, want model", next2)
	}
	if got.controlPage.jogScale != jogBaseScale {
		t.Errorf("jogScale = %v, want %v", got.controlPage.jogScale, jogBaseScale)
	}
}

func TestUpdateControlPage_Jog(t *testing.T) {
	tests := []struct {
		name               string
		seed               model
		key                tea.KeyPressMsg
		wantTargetCursor   []float64
		wantNewLastJogTime bool
		wantCmd            cmdRegime
	}{
		{
			name: "+ on DomainNone gets swallowed",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					selected: 0, nSelectable: 3, selectionDomain: DomainNone,
					targetCursor: []float64{},
					touched:      []bool{},
				},
			},
			key:                tea.KeyPressMsg{Text: "+"},
			wantTargetCursor:   []float64{},
			wantNewLastJogTime: false,
			wantCmd:            cmdNone,
		},
		{
			name: "+ when nSelectable = 0 gets swallowed",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					selected: 0, nSelectable: 0, selectionDomain: DomainTask,
					targetCursor: []float64{},
					touched:      []bool{},
				},
			},
			key:                tea.KeyPressMsg{Text: "+"},
			wantTargetCursor:   []float64{},
			wantNewLastJogTime: false,
			wantCmd:            cmdNone,
		},
		{
			name: "+ on DomainJoint updates targetCursor and fires",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					selected: 1, nSelectable: 6, selectionDomain: DomainJoint,
					targetCursor: make([]float64, 6),
					touched:      make([]bool, 6),
				},
			},
			key:                tea.KeyPressMsg{Text: "+"},
			wantTargetCursor:   []float64{0.0, 0.0 + jogStepRadians, 0.0, 0.0, 0.0, 0.0},
			wantNewLastJogTime: true,
			wantCmd:            cmdOpaque,
		},
		{
			name: "+ on DomainTask updates targetCursor and fires",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					selected: 2, nSelectable: 3, selectionDomain: DomainTask,
					targetCursor: []float64{0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.1},
					touched:      make([]bool, 7),
				},
			},
			key:                tea.KeyPressMsg{Text: "+"},
			wantTargetCursor:   []float64{0.1, 0.2, 0.3 + jogStepMeters, 0.0, 0.0, 0.0, 0.1},
			wantNewLastJogTime: true,
			wantCmd:            cmdOpaque,
		},
		{
			name: "- on DomainTask updates targetCursor and fires",
			seed: model{
				activePage: pageControl,
				controlPage: controlPage{
					selected: 2, nSelectable: 3, selectionDomain: DomainTask,
					targetCursor: []float64{0.1, 0.2, 0.3, 0.0, 0.0, 0.0, 0.1},
					touched:      make([]bool, 7),
				},
			},
			key:                tea.KeyPressMsg{Text: "-"},
			wantTargetCursor:   []float64{0.1, 0.2, 0.3 - jogStepMeters, 0.0, 0.0, 0.0, 0.1},
			wantNewLastJogTime: true,
			wantCmd:            cmdOpaque,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			// no deep clones on tc.seed required because we never
			// compare got's targetCursor or touched arrays to tc.seed's arrays
			before := time.Now()
			next, cmd := tc.seed.Update(tc.key)
			after := time.Now()
			got, ok := next.(model)
			if !ok {
				t.Fatalf("Updated = %v, want model", next)
			}

			checkCommand(t, cmd, tc.wantCmd)

			targetCursorsEqual := slices.EqualFunc(got.controlPage.targetCursor, tc.wantTargetCursor, func(a, b float64) bool {
				return math.Abs(a-b) < 1e-9
			})
			if !targetCursorsEqual {
				t.Errorf("targetCursor = %v, want %v", got.controlPage.targetCursor, tc.wantTargetCursor)
			}

			if tc.wantNewLastJogTime {
				if got.controlPage.lastJogTime.Before(before) {
					t.Errorf("lastJogTime = %v, want after %v", got.controlPage.lastJogTime, before)
				}
				if got.controlPage.lastJogTime.After(after) {
					t.Errorf("lastJogTime = %v, want before %v", got.controlPage.lastJogTime, after)
				}
			} else {
				if !got.controlPage.lastJogTime.Equal(tc.seed.controlPage.lastJogTime) {
					t.Errorf("lastJogTime = %v, want %v", got.controlPage.lastJogTime, tc.seed.controlPage.lastJogTime)
				}
			}
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

			now := time.Now()
			got.jogCursor(tc.jogSteps, now)

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
				if !got.lastJogTime.Equal(now) {
					t.Errorf("lastJogTime = %v, want after %v", got.lastJogTime, now)
				}
			} else {
				if !got.lastJogTime.Equal(tc.seed.lastJogTime) {
					t.Errorf("lastJogTime = %v, want %v", got.lastJogTime, tc.seed.lastJogTime)
				}
			}
		})
	}
}

func TestControlPage_JogRamp(t *testing.T) {
	tests := []struct {
		name string
		seed *controlPage
		jogs []struct {
			steps int
			delay time.Duration
		}
		wantTargetCursor    []float64
		wantLastJogDir      int
		wantLastJogSelected int
		wantJogScale        float64
	}{
		{
			name: "first jog with scale 1.0",
			seed: &controlPage{
				nSelectable: 3, selected: 2, selectionDomain: DomainTask,
				lastJogSelected: 2, lastJogDir: 1, jogScale: 1.0,
				targetCursor: make([]float64, 3), touched: make([]bool, 3),
			},
			jogs: []struct {
				steps int
				delay time.Duration
			}{
				{steps: 1, delay: jogRampTimeout + time.Second},
			},
			wantTargetCursor:    []float64{0.0, 0.0, jogStepMeters},
			wantLastJogDir:      1,
			wantLastJogSelected: 2,
			wantJogScale:        1.0,
		},
		{
			name: "second jog arrives before timout ramps up",
			seed: &controlPage{
				nSelectable: 3, selected: 2, selectionDomain: DomainTask,
				lastJogSelected: 2, lastJogDir: 1, jogScale: 1.0,
				targetCursor: make([]float64, 3), touched: make([]bool, 3),
			},
			jogs: []struct {
				steps int
				delay time.Duration
			}{
				{steps: 1, delay: jogRampTimeout + time.Second},
				{steps: 1, delay: time.Millisecond * 20},
			},
			wantTargetCursor:    []float64{0.0, 0.0, jogStepMeters * (1 + 1 + jogRampAlpha)},
			wantLastJogDir:      1,
			wantLastJogSelected: 2,
			wantJogScale:        1.0 + jogRampAlpha,
		},
		{
			name: "second jog arrives after timout resets scale",
			seed: &controlPage{
				nSelectable: 3, selected: 2, selectionDomain: DomainTask,
				lastJogSelected: 2, lastJogDir: 1, jogScale: 1.0,
				targetCursor: make([]float64, 3), touched: make([]bool, 3),
			},
			jogs: []struct {
				steps int
				delay time.Duration
			}{
				{steps: 1, delay: jogRampTimeout + time.Second},
				{steps: 1, delay: jogRampTimeout + time.Second},
			},
			wantTargetCursor:    []float64{0.0, 0.0, jogStepMeters * 2},
			wantLastJogDir:      1,
			wantLastJogSelected: 2,
			wantJogScale:        1.0,
		},
		{
			name: "reverse jog resets scale",
			seed: &controlPage{
				nSelectable: 3, selected: 2, selectionDomain: DomainTask,
				lastJogSelected: 2, lastJogDir: 1, jogScale: 1.0,
				targetCursor: make([]float64, 3), touched: make([]bool, 3),
			},
			jogs: []struct {
				steps int
				delay time.Duration
			}{
				{steps: 1, delay: jogRampTimeout + time.Second},
				{steps: -1, delay: time.Millisecond * 20},
			},
			wantTargetCursor:    []float64{0.0, 0.0, 0.0},
			wantLastJogDir:      -1,
			wantLastJogSelected: 2,
			wantJogScale:        1.0,
		},
		{
			name: "selection change resets scale",
			seed: &controlPage{
				nSelectable: 3, selected: 2, selectionDomain: DomainTask,
				lastJogSelected: 1, lastJogDir: 1, jogScale: 2.0,
				targetCursor: make([]float64, 3), touched: make([]bool, 3),
			},
			jogs: []struct {
				steps int
				delay time.Duration
			}{
				{steps: 1, delay: time.Millisecond * 20},
			},
			wantTargetCursor:    []float64{0.0, 0.0, jogStepMeters},
			wantLastJogDir:      1,
			wantLastJogSelected: 2,
			wantJogScale:        1.0,
		},
		{
			name: "consecutive jogs saturate at max",
			seed: &controlPage{
				nSelectable: 3, selected: 2, selectionDomain: DomainTask,
				lastJogSelected: 2, lastJogDir: 1, jogScale: 0.95 * jogMaxScale,
				targetCursor: make([]float64, 3), touched: make([]bool, 3),
			},
			jogs: []struct {
				steps int
				delay time.Duration
			}{
				{steps: 1, delay: time.Millisecond * 20},
				{steps: 1, delay: time.Millisecond * 20},
				{steps: 1, delay: time.Millisecond * 20},
				{steps: 1, delay: time.Millisecond * 20},
				{steps: 1, delay: time.Millisecond * 20},
			},
			wantTargetCursor:    []float64{0.0, 0.0, 5 * jogMaxScale * jogStepMeters},
			wantLastJogDir:      1,
			wantLastJogSelected: 2,
			wantJogScale:        jogMaxScale,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := *tc.seed
			got.targetCursor = slices.Clone(tc.seed.targetCursor)
			got.touched = slices.Clone(tc.seed.touched)

			base := time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC)
			got.lastJogTime = base
			now := base
			for _, jog := range tc.jogs {
				now = now.Add(jog.delay)
				got.jogCursor(jog.steps, now)
			}

			targetCursorsEqual := slices.EqualFunc(got.targetCursor, tc.wantTargetCursor, func(a, b float64) bool {
				return math.Abs(a-b) < 1e-9
			})
			if !targetCursorsEqual {
				t.Errorf("targetCursor = %v, want %v", got.targetCursor, tc.wantTargetCursor)
			}
			if got.lastJogDir != tc.wantLastJogDir {
				t.Errorf("lastJogDir = %v, want %v", got.lastJogDir, tc.wantLastJogDir)
			}
			if got.lastJogSelected != tc.wantLastJogSelected {
				t.Errorf("lastJogSelected = %v, want %v", got.lastJogSelected, tc.wantLastJogSelected)
			}
			if math.Abs(got.jogScale-tc.wantJogScale) > 1e-9 {
				t.Errorf("jogScale = %v, want %v", got.jogScale, tc.wantJogScale)
			}
		})
	}
}
