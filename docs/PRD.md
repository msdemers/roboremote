# roboremote — Product Requirements Document

## Overview
roboremote is an open source robotic arm simulation platform with real-time remote interaction. A physics sidecar simulates arm dynamics; a Go gRPC server distributes state to multiple simultaneous clients; clients include a TUI monitor and a dev-only Viser visualizer; an interactive 3D visualizer is planned for V2.

## Goals
- Demonstrate real-time gRPC streaming architecture in Go
- Provide an accessible, containerized robot sim anyone can run locally
- Enable live interaction with a simulated arm (monitoring, commanding)
- Build toward physical robot teleoperation (future)

## Non-Goals (v1)
- Cloud deployment (v2)
- Interactive 3D visualizer with tugging (V2)
- Real hardware integration (future)
- Model Switcher with multiple, popular robot models (future)
- User-placeable sensor nodes (position/attitude/velocity) (v2)

## Target Users
- Robotics/ML researchers wanting a lightweight sim sandbox
- Developers learning real-time Go backend architecture and teleoperation of remote devices
- Hobbyists with or interested in the SO-ARM100 physical kit

## Robot Model
SO-ARM100 / SO101 (5 DOF + gripper)
- URDF and MJCF available, open source, community vetted
- Affordable physical kit (~$100) for real hardware follow-on
- so101_new_calib.urdf is the canonical URDF

## V1 Deliverables
1. Physics sidecar (Python, Pinocchio or MuJoCo) — dynamics, FK, control policies
2. Sim server (Go, gRPC) — state distribution, client fan-out, command routing
3. TUI client (Go, Bubble Tea) — monitor connection, state, control
4. Dev-only Visualizer (Python, Pinocchio `ViserVisualizer`) — passive 3D rendering for development and debugging; opt-in via `docker compose --profile viz`
5. Docker Compose orchestration — single `docker compose up` runs full stack

## V2 Deliverables (DevOps capstone or fast follow)
- Fly.io deployment (two separate apps over private network)
- GitHub Actions CI/CD pipeline
- Public demo URL

## Success Criteria (v1)
- `docker compose up` starts physics and server cleanly; TUI attaches
  separately (a TTY app can't be silently backgrounded like the other two) —
  either `docker compose run --rm tui` (no Go toolchain needed) or natively
  via `go run ./tui/cmd/robotui` / a built `robotui`
- TUI displays live joint state updating in real time
- User can switch control policies from TUI
- User can set joint-space and task-space (Cartesian) targets from the TUI
- Dev visualizer (Viser) renders live arm state for development validation