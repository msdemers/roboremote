# roboremote — Product Requirements Document

## Overview
roboremote is an open source robotic arm simulation platform with real-time
remote interaction. A physics sidecar simulates arm dynamics; a Go gRPC server
distributes state to multiple simultaneous clients; clients include a TUI
monitor and a 3D interactive visualizer.

## Goals
- Demonstrate real-time gRPC streaming architecture in Go
- Provide an accessible, containerized robot sim anyone can run locally
- Enable live interaction with a simulated arm (monitoring, commanding, tugging)
- Build toward physical robot teleoperation (future)

## Non-Goals (v1)
- Cloud deployment (v2)
- Real hardware integration (future)
- Inverse kinematics solver (future)
- Multi-arm simulation (future)

## Target Users
- Robotics/ML researchers wanting a lightweight sim sandbox
- Developers learning real-time Go backend architecture
- Hobbyists with or interested in the SO-ARM100 physical kit

## Robot Model
SO-ARM100 / SO101 (5 DOF + gripper)
- URDF and MJCF available, open source, community vetted
- Affordable physical kit (~$100) for real hardware follow-on

## V1 Deliverables
1. Physics sidecar (Python, Pinocchio) — dynamics, FK, control policies
2. Sim server (Go, gRPC) — state distribution, client fan-out, command routing
3. TUI client (Go, Bubble Tea) — monitor connection, state, control, sensor nodes
4. Docker Compose orchestration — single `docker compose up` runs full stack

## V2 Deliverables (DevOps capstone or fast follow)
- Fly.io deployment (two separate apps over private network)
- GitHub Actions CI/CD pipeline
- Public demo URL

## Success Criteria (v1)
- `docker compose up` starts all three services cleanly
- TUI displays live joint state updating in real time
- User can switch control policies from TUI
- User can place a sensor node and see its world-frame pose update live
- 3D visualizer stub documented with clear extension path