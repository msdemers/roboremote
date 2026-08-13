package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"

	tea "charm.land/bubbletea/v2"
	armv1 "github.com/msdemers/roboremote/proto/gen/go/roboremote/arm/v1"
	"github.com/msdemers/roboremote/tui/internal/app"
	sim "github.com/msdemers/roboremote/tui/internal/simclient"
)

const (
	defaultAddr = "localhost:50051"
	addrEnv     = "ROBOREMOTE_SERVER_ADDR"
)

var debugFlag = flag.Bool("debug", false, "log to debug.log for troubleshooting")

func main() {
	flag.Usage = func() {
		out := flag.CommandLine.Output()
		fmt.Fprintf(out, `
robotui — terminal client for the roboremote sim server

Usage:
robotui [flags] [address]

Address is resolved in this order:
1. positional argument
2. %s environment variable
3. built-in default (%s)

Flags:
`, addrEnv, defaultAddr)
		flag.PrintDefaults()
	}

	flag.Parse()

	relayAddr, addrSource := resolveAddr()

	if *debugFlag {
		f, err := tea.LogToFile("debug.log", "debug")
		if err != nil {
			log.Fatalln("failed to configure tea logging")
		}
		defer f.Close()
	}

	streamRate := armv1.StreamRate_STREAM_RATE_UNSPECIFIED

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sim, err := sim.New(ctx, relayAddr)
	if err != nil {
		log.Fatalf("failed to connect to sim relay server: %v", err)
	}
	defer sim.Close()

	p := tea.NewProgram(app.New(sim, streamRate, addrSource))

	if _, err := p.Run(); err != nil {
		log.Fatalf("shutting down: %v", err)
	}
}

func resolveAddr() (addr, source string) {
	if a := flag.Arg(0); a != "" {
		return a, "argument"
	}
	if a := os.Getenv(addrEnv); a != "" {
		return a, addrEnv
	}
	return defaultAddr, "default"
}
