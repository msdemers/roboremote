package main

import (
	"fmt"

	"charm.land/bubbles/v2/spinner"
	tea "charm.land/bubbletea/v2"
	lipgloss "charm.land/lipgloss/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

func main() {

	// placeholders to verify go dependencies
	var _ = armv1.StreamEnvelope{}
	var _ = tea.Model(nil)
	var _ = lipgloss.Blue
	var _ = spinner.Model{}
	fmt.Println("presence of initial go dependencies verified")
}
