package relay

import (
	"testing"
	"time"

	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
)

func recvWithin(t *testing.T, ch <-chan *armv1.StreamEnvelope, d time.Duration) *armv1.StreamEnvelope {
	t.Helper()
	select {
	case f := <-ch:
		return f
	case <-time.After(d):
		t.Fatal("timed out waiting for frame")
		return nil
	}
}

func TestFanOut(t *testing.T) {
	h := NewHub()
	go h.Run()

	h.frames <- &armv1.StreamEnvelope{} // frame 0 gets cached/swallowed as the descriptor

	const N = 3
	var subs []<-chan *armv1.StreamEnvelope
	for i := 0; i < N; i++ {
		_, frames, unsub := h.Subscribe(1)
		defer unsub()
		subs = append(subs, frames)
	}

	armState := &armv1.StreamEnvelope{}
	h.frames <- armState // send arm state to hub for broadcast

	for i, frames := range subs {
		if got := recvWithin(t, frames, time.Second); got != armState {
			t.Errorf("sub %d: got %p, want %p", i, got, armState)
		}
	}

}

func barrier(h *Hub) { // a function exclusively for guaranteeing sync for frame-rate testing
	// create throw away client to control sync/rest of channel select clause
	_, _, unsub := h.Subscribe(1) // guarantees that case subscribe will consume a select clause cycle
	// the broadcast loop over the whole subs map is guaranteed to be complete by now.
	unsub() // throw away the barrier client/subscriber
}

type channelCount struct {
	ch  <-chan *armv1.StreamEnvelope
	got int
}

func TestFrameRates(t *testing.T) {
	h := NewHub()
	go h.Run()

	h.frames <- &armv1.StreamEnvelope{} // frame 0 gets cached/swallowed as the descriptor

	decimations := []int{1, 2, 4}
	decToCountMap := map[int]*channelCount{}
	for _, n := range decimations {
		_, frames, unsub := h.Subscribe(n)
		defer unsub()
		decToCountMap[n] = &channelCount{ch: frames, got: 0}
	}

	for i := 0; i < 4; i++ {
		h.frames <- &armv1.StreamEnvelope{}
		barrier(h) // force wait on frame i to fully broadcast
		for _, chanCount := range decToCountMap {
			select {
			case <-chanCount.ch:
				chanCount.got++
			default:
			}
		}

	}

	for n, chanCount := range decToCountMap {
		got := chanCount.got
		want := 4 / n
		if got != want {
			t.Errorf("subscriber with decimation %d got %d frames, want %d", n, got, want)
		}
	}
}
