package app

import (
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
)

func key(s string) tea.KeyPressMsg {
	return tea.KeyPressMsg{Text: s}
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
			seed:            model{activePage: pageControl, pendingConfirm: confirmReset},
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

			switch tc.wantCmd {
			case cmdNone:
				if cmd != nil {
					t.Errorf("Update() returned a cmd when nil expected")
				}
			case cmdQuit:
				msg := cmd()
				if _, ok := msg.(tea.QuitMsg); !ok {
					t.Errorf("Update() returned %T, expected %T", msg, tea.QuitMsg{})
				}
			case cmdOpaque:
				if cmd == nil {
					t.Errorf("Update() returned nil cmd, expected non nil")
				}
			}

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
