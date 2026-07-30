package main

import (
	"context"
	"flag"
	"log"
	"os"

	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"github.com/msdemers/roboremote/tui/internal/app"
	sim "github.com/msdemers/roboremote/tui/internal/simclient"
)

func main() {
	debug := flag.Bool("debug", false, "log to debug.log for troubleshooting")
	flag.Parse()

	if *debug {
		f, err := tea.LogToFile("debug.log", "debug")
		if err != nil {
			log.Fatalln("failed to configure tea logging")
		}
		defer f.Close()
	}

	relayAddr := os.Getenv("SERVER_ADDR")
	if relayAddr == "" {
		relayAddr = "localhost:50051"
	}

	streamRate := armv1.StreamRate_STREAM_RATE_UNSPECIFIED

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sim, err := sim.New(ctx, relayAddr)
	if err != nil {
		log.Fatalf("faile to connect to sim relay server: %v", err)
	}
	defer sim.Close()

	p := tea.NewProgram(app.New(sim, streamRate))

	if _, err := p.Run(); err != nil {
		log.Fatalf("shutting down: %v", err)
	}
}
