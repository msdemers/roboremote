package app

import (
	"charm.land/bubbles/v2/table"
)

func (m model) viewMonitorPage() string {
	rows := toTableRows(jointRows(m.descriptor, m.armState))
	jt := table.New(
		table.WithColumns(tableColumns()),
		table.WithWidth(tableWidth(tableColumns())),
		table.WithHeight(len(rows)+1),
		table.WithRows(rows),
	)
	return jt.View()
}
