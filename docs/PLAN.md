# roboremote — Project Plan

## Status Legend
- [ ] Not started
- [~] In progress  
- [x] Complete

## Phase 0: Design (Complete)
- [x] Define project concept and goals
- [x] Choose architecture: gRPC, physics sidecar pattern, multi-client
- [x] Choose robot model: SO-ARM100 / SO101
- [x] Choose physics engine: Pinocchio v1, MuJoCo fast follow
- [x] Choose hosting strategy: Docker Compose v1, Fly.io v2
- [x] Design repo structure
- [x] Sketch proto file: `proto/arm.proto`
- [x] Draft PRD, PLAN, DECISIONS docs

## Phase 1: Repo Initialization
- [x] Initialize git repo: `roboremote`
- [x] Create directory skeleton
- [x] Initialize Go modules (server, tui)
- [x] Stub entry points (main.go, main.py)
- [x] Stub Dockerfiles (server, physics, tui)
- [x] Stub docker-compose.yml
- [x] Stub .env.example
- [x] Stub Makefile
- [x] Stub deploy/ with README and fly.toml.example files
- [x] Stub viz/ with README
- [x] Commit: "chore: initialize repo structure"

## Phase 2: Proto and Code Generation
- [x] Write proto/arm.proto (drafted, needs final review)
- [x] Install and configure buf
- [x] Write buf.gen.yaml
- [x] Generate Go stubs → proto/gen/go/
- [x] Generate Python stubs → proto/gen/python/
- [x] Commit: "feat: add arm.proto and generated stubs"

## Phase 3: Physics Sidecar
- [x] Download SO101 URDF/MJCF → models/so101/
- [x] uv init and dependency setup
- [x] Install Pinocchio
- [x] Test simple script to verify model loads and meets so101 expectations
- [ ] Implement FK wrapper
- [ ] Implement gravity compensation policy
- [ ] Implement joint PD policy
- [ ] Implement fixed-step integrator
- [ ] Implement gRPC server (physics side)
- [ ] Containerize and verify headless
- [ ] Commit: "feat: physics sidecar v1"

## Phase 4: Sim Server
- [ ] Implement gRPC server skeleton
- [ ] Implement simulation loop goroutine
- [ ] Implement state broadcaster (fan-out to N clients)
- [ ] Implement SimStream RPC handler
- [ ] Implement GetArmState RPC handler
- [ ] Implement SetControlMode RPC handler
- [ ] Implement SensorNode world-pose computation
- [ ] Containerize and verify
- [ ] Commit: "feat: sim server v1"

## Phase 5: TUI Client
- [ ] Initialize Bubble Tea app structure
- [ ] Implement gRPC stream consumer
- [ ] Implement connection status panel
- [ ] Implement joint state monitor panel
- [ ] Implement control input monitor panel
- [ ] Implement sensor node manager panel
- [ ] Implement control policy switcher
- [ ] Containerize with TTY support
- [ ] Commit: "feat: tui client v1"

## Phase 6: Dev Visualizer (Rerun)
- [ ] Install Rerun Python SDK in physics environment
- [ ] Write Rerun bridge script (consumes gRPC stream, logs to Rerun viewer)
- [ ] Verify live arm state renders correctly
- [ ] Commit: "feat: add rerun dev visualizer bridge"

## Phase 7: Integration and Polish
- [ ] Full stack smoke test via docker compose up
- [ ] Write README.md (purpose, quickstart, architecture diagram)
- [ ] Record demo (gif or video)
- [ ] Commit: "docs: readme, architecture diagram, and demo"

## Phase 8: V2 Deployment (DevOps capstone or fast follow)
- [ ] Write fly.toml for server and physics apps
- [ ] Configure fly secrets for environment variables
- [ ] Set up GitHub Actions CI/CD
- [ ] Deploy to Fly.io, verify private network gRPC
- [ ] Update README with public demo URL

## Open TODOs
- [ ] V2: Design interactive 3D visualizer (Three.js, browser-based, tugging support)
- [ ] V2: Evaluate AWS vs CoreWeave for GPU/Isaac work
- [ ] Survey quaternion conventions/ordering across spatial SDKs (MuJoCo, NVIDIA
      Isaac, Apple ARKit/RealityKit, Unity) to inform proto `Pose` format; keep it
      vendor-neutral, not locked to Pinocchio. Only the SE3→Pose helper changes.