package app

import (
	"fmt"

	"charm.land/bubbles/v2/table"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

type jointRow struct {
	Name        string
	Coordinates []float64
	Velocities  []float64
	Efforts     []float64
}

func jointRows(desc *armv1.ModelDescriptor, state *armv1.ArmState) []jointRow {
	jRows := make([]jointRow, 0, len(desc.Joints))

	for _, j := range desc.Joints {
		row := jointRow{
			Name:        j.Name,
			Coordinates: state.GetQ().GetQ()[j.GetIdxQ() : j.GetIdxQ()+j.GetNq()],
			Velocities:  state.GetV().GetV()[j.GetIdxV() : j.GetIdxV()+j.GetNv()],
			Efforts:     state.GetTau().GetTau()[j.GetIdxV() : j.GetIdxV()+j.GetNv()],
		}
		jRows = append(jRows, row)
	}

	return jRows
}

func cellAt(vals []float64, i int) string {
	if i >= len(vals) {
		return ""
	}
	return fmt.Sprintf("%.2f", vals[i])
}

func toTableRows(rows []jointRow) []table.Row {
	var tableRows []table.Row
	for _, jRow := range rows {
		n := max(len(jRow.Coordinates), len(jRow.Velocities))
		for i := 0; i < n; i++ {
			rowLabel := ""
			if i == 0 {
				rowLabel = jRow.Name
			}
			tableRows = append(tableRows, table.Row{
				rowLabel,
				cellAt(jRow.Coordinates, i),
				cellAt(jRow.Velocities, i),
				cellAt(jRow.Efforts, i),
			})
		}
	}
	return tableRows
}

func tableColumns() []table.Column {
	return []table.Column{
		{Title: "Name", Width: 14},
		{Title: "Position (q)", Width: 14},
		{Title: "Velocity (v)", Width: 14},
		{Title: "Effort (τ)", Width: 14},
	}
}

func tableWidth(cols []table.Column) int {
	w := 0
	for _, c := range cols {
		w += c.Width
	}
	return w
}

func validateDescriptor(desc *armv1.ModelDescriptor) error {
	for _, j := range desc.Joints {
		if j.GetIdxQ()+j.GetNq() > desc.GetNq() || j.GetIdxV()+j.GetNv() > desc.GetNv() {
			return fmt.Errorf("a joint, %s, has out of bounds state indices", j.GetName())
		}
	}
	return nil
}

func validateFrameShape(desc *armv1.ModelDescriptor, state *armv1.ArmState) error {
	if len(state.GetQ().GetQ()) != int(desc.GetNq()) {
		return fmt.Errorf("frame has %d coordinates, model expects %d", len(state.GetQ().GetQ()), desc.GetNq())
	}

	if len(state.GetV().GetV()) != int(desc.GetNv()) {
		return fmt.Errorf("frame has %d velocities, model expects %d", len(state.GetV().GetV()), desc.GetNv())
	}

	if len(state.GetTau().GetTau()) != int(desc.GetNv()) {
		return fmt.Errorf("frame has %d efforts (tau), model expects %d", len(state.GetTau().GetTau()), desc.GetNv())
	}

	return nil
}
