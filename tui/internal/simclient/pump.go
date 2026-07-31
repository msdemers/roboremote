package simclient

import (
	"context"
	"errors"
	"time"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

const sendTimeout = 1 * time.Second

type CommandKind int

const (
	KindSetMode CommandKind = iota
	KindSetTarget
	KindReset
)

type queuedCmd struct {
	kind CommandKind
	mode armv1.ControlMode
}

type CommandResult struct {
	Kind CommandKind
	Err  error
}

var ErrBacklogged = errors.New("command queue full: pump is not draining")

func (c *Client) SubmitMode(m armv1.ControlMode) {
	select {
	case c.discreteCmds <- queuedCmd{kind: KindSetMode, mode: m}: // had room
	default:
		// Queue full means the pump is stuck (hung sends) AND the operato
		// is mashing keys. Never block the UI; surface it as a result so
		// the footer shows the truth.
		select {
		case c.results <- CommandResult{Kind: KindSetMode, Err: ErrBacklogged}:
		default: // if even the results queue back up, just persist the previous backlog info
		}

	}
}

func (c *Client) SubmitTarget(target *armv1.SetTargetRequest) {
	// drain-then-replace idiom for latest winds "slot"
	select {
	case c.latestTarget <- target: // slot was empty. Newest target stored
	default: // slot already holds a stale, unsent target
		select {
		case <-c.latestTarget: // discard the existing, stale data
		default: // unless it's already been emptied
		}
		c.latestTarget <- target // make sure we end with a full slot
	}
}

func (c *Client) SubmitReset() {
	select {
	case c.discreteCmds <- queuedCmd{kind: KindReset}: // had room
	default:
		// Queue full means the pump is stuck (hung sends) AND the operato
		// is mashing keys. Never block the UI; surface it as a result so
		// the footer shows the truth.
		select {
		case c.results <- CommandResult{Kind: KindReset, Err: ErrBacklogged}:
		default: // if even the results queue back up, just persist the previous backlog info
		}
	}
}

func (c *Client) Results() <-chan CommandResult {
	return c.results
}

func (c *Client) sendDiscrete(comm queuedCmd) {
	ctx, cancel := context.WithTimeout(c.ctx, sendTimeout)
	defer cancel()

	var err error
	switch comm.kind {
	case KindSetMode:
		_, err = c.stub.SetControlMode(ctx, &armv1.SetControlModeRequest{Mode: comm.mode})
	case KindReset:
		_, err = c.stub.ResetConfiguration(ctx, &armv1.ResetConfigurationRequest{})
	}
	c.results <- CommandResult{Kind: comm.kind, Err: err}
}

func (c *Client) sendTarget(target *armv1.SetTargetRequest) {
	ctx, cancel := context.WithTimeout(c.ctx, sendTimeout)
	defer cancel()
	_, err := c.stub.SetTarget(ctx, target)
	c.results <- CommandResult{Kind: KindSetTarget, Err: err}
}

func (c *Client) pump() {
	for {
		select {
		case <-c.ctx.Done():
			return

		case comm := <-c.discreteCmds:
			c.sendDiscrete(comm)

		case t := <-c.latestTarget:
			c.sendTarget(t)
		}
	}
}
