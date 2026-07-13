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
- [x] Write proto/arm.proto (redesigned + linting clean; ADR-008..016)
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
- [x] Implement FK wrapper
- [x] Implement gravity compensation policy
- [x] Implement fixed-step integrator (semi-implicit Euler; convergence-tested)
- [x] Test: gravity comp holds arbitrary config at rest (zero-g equilibrium) —
      static-equilibrium test in sim/test_integrator.py
- [x] Implement sim loop (Simulator owns model/data/state; tick() advances
      integrator + injected policy; run()/stop() paced via threading.Event; void
      tick + get_snapshot() producer/consumer split; drives own clock per ADR-007)
- [x] Implement control policies (task-space EE PD, compensated PD) — composable
      torque terms summed into behaviors (see ADR pending)
- [x] Implement gRPC server (physics side)
- [x] Commit: physics sidecar v1 (control + gRPC complete, tested)
      - Containerization + headless verify deferred and batched into Phase 5 (done
        once for all services; ADR-017 durable gen-code distribution lands there).

## Phase 4: Sim Server
- [ ] Implement gRPC server skeleton
- [ ] Implement state relay pump (subscribe to sidecar stream; per ADR-007 Go is a
      pure relay, not an integrator)
- [ ] Implement state broadcaster (fan-out to N clients)
- [ ] Implement Subscribe RPC handler (server-stream; descriptor-first, ADR-010)
- [ ] Implement unary command handlers: SetControlMode, SetTarget,
      ResetConfiguration (ADR-008, ADR-013)
- [ ] Commit: "feat: sim server v1"

## Phase 5: TUI Client
- [ ] Initialize Bubble Tea app structure
- [ ] Implement gRPC stream consumer
- [ ] Implement connection status panel
- [ ] Implement joint state monitor panel
- [ ] Implement control input monitor panel
- [ ] Implement control policy switcher
- [ ] Commit: "feat: tui client v1"

### Containerization (batched — all services; was split across Phases 3–5)
- [ ] Durable generated-code distribution (ADR-017): package `roboremote-proto` as an
      installable Python dep; resolve Go `proto/gen/go` via `go.work`/module for
      server + tui; set Docker build context to repo root so stubs land in images.
- [ ] Physics sidecar image (headless — Pinocchio needs no display; MODEL_PATH env)
- [ ] Sim server image (scratch-based, CGO-free per ADR-002)
- [ ] TUI client image (TTY support)
- [ ] docker-compose.yml: server↔sidecar internal network, env-var addresses (ADR-002/006)
- [ ] Verify `docker compose up` brings the full stack up cleanly
- [ ] Commit: "build: containerize full stack"

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
- [ ] V2: User-placeable sensor nodes (position/attitude/velocity), physics-side
      world pose + spatial velocity, add/remove lifecycle (deferred per ADR-012)
- [ ] V2: Design interactive 3D visualizer (Three.js, browser-based, tugging support)
- [ ] V2: Evaluate AWS vs CoreWeave for GPU/Isaac work
- [x] Survey quaternion conventions/ordering across spatial SDKs (MuJoCo, NVIDIA
      Isaac, Apple ARKit/RealityKit, Unity) to inform proto `CartesianPose` format.
      Resolved → ADR-011: scalar-last `{x, y, z, w}` (industry majority; matches
      Eigen/Pinocchio coeff order). Only the SE3→CartesianPose helper converts.
- [ ] Integrator accuracy/stability: semi-implicit Euler is first-order and only
      marginally stable at the 1 ms control period for undamped free-swing dynamics
      (energy band ~7%, destabilizes over seconds). Fine for controlled motion
      (gravity comp / PD add effective damping). Revisit a higher-order or substepped
      integrator (RK4, semi-implicit substepping) if aggressive/long free-running sim
      is needed.
- [ ] Task-space orientation / full-pose control (V1 is position-only 3-DOF per
      ADR-020; arm is kinematically deficient for SE(3)). Add on a specific
      workspace need with reduced-orientation or non-deficient handling.
- [ ] Variable damping λ(σ_min) for the operational-space inertia (Nakamura/Wampler
      damped least squares; V1 uses constant λ per ADR-020) — removes constant-λ
      tracking bias in the well-conditioned interior.
- [ ] Null-space posture task + inertia-weighted null-space damping (V1 uses plain
      velocity damping projected into the null space per ADR-020).
- [ ] Pinocchio compute/caching "realization layer": a Stage-style
      (position/velocity/acceleration, à la Simbody) wrapper over `data` that
      sequences the recursions once and enforces cache validity — Pinocchio caches
      like Simbody but without invalidation guardrails. Removes redundant passes
      (e.g. the extra end_effector_pose FK). Scoped as a kinematics/ + dynamics/
      refactor.