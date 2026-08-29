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

## Phase 4: Sim Server (Complete)
- [x] Implement gRPC server skeleton
- [x] Implement state relay pump (subscribe to sidecar stream; per ADR-007 Go is a
      pure relay, not an integrator)
- [x] Implement state broadcaster (fan-out to N clients) — channel-serialized hub
      (server/internal/relay), latest-value-wins per-subscriber slots (ADR-009)
- [x] Implement Subscribe RPC handler (server-stream; descriptor-first, ADR-010)
- [x] Implement unary command handlers: SetControlMode, SetTarget,
      ResetConfiguration (ADR-008, ADR-013) — verbatim forwards, bypass the hub
- [x] Hub unit tests: fan-out + per-client decimation (barrier-synchronized, no sleeps)
- [x] Committed as per-slice commits (not one "feat: sim server v1")
- [ ] Deferred hardening (not v1-blocking): pump reconnection (sidecar restart →
      hub goes silent today); graceful shutdown (signal handling + Run()/pump stop +
      cancelable pump ctx — log.Fatalf currently skips defers)

## Phase 5: TUI Client
- [x] Initialize Bubble Tea app structure — bubbletea/v2 + bubbles/v2 + lipgloss/v2;
      `internal/app` split by Elm role (model/msgs/update/view/cmds), `internal/stream`
      owns the gRPC bridge
- [x] Implement gRPC stream consumer — goroutine+channel bridge (`stream.Connect`),
      descriptor-gated 3-state lifecycle (Connecting/Streaming/Disconnected per
      ADR-010's descriptor-first rule), live `sim_time` verified end-to-end against
      a running server + physics sidecar
- [x] Implement connection status panel — bordered header box (`header.go`):
      title, address, model name, per-lifecycle contextual badges
      (CONNECTING/STREAMING/DISCONNECTED), live-sized to terminal width via
      `tea.WindowSizeMsg`; full-window rendering via `tea.View.AltScreen`
- [x] Implement joint state monitor panel — `bubbles/table` of per-DOF q/v/tau
      (`joints.go`), row-per-DOF (not row-per-joint) to handle `Nq != Nv`
      correctly, validated against descriptor bounds/frame-shape before display
- [x] Implement page switcher — tab bar chrome + per-page keymaps (ADR-021)
- [x] Implement persistent footer — global key hints + command status line (ADR-021)
- [x] Implement command pump in internal/simclient (ADR-021)
- [x] Implement Control page — mode switcher, state strip, page key hints
      (ADR-013, ADR-021)
- [x] Implement jog target entry — local cursor + idle resync (ADR-021)
- [x] Implement modal confirm — quit and reset, deadline-guarded timeout (ADR-021)
- [x] Confirm dialog timeout indicator — draining bar, frame-driven (ADR-021)
- [x] Committed as per-slice commits (not one "feat: tui client v1")
- [ ] Deferred polish (not v1-blocking): map gRPC status codes to human badge text
      (`describeErr`, pure, beside `disconnectedBadge`); raw error to debug.log
- [ ] `simclient.Subscribe`'s error-frame send (stream.go) is unguarded — blocks if
      abandoned; unreachable today (no reconnect), same bucket as Phase 4's pump
      reconnection gap

### Containerization (batched — all services; was split across Phases 3–5) (Complete)
- [x] Durable generated-code distribution (ADR-017)
- [x] Root `.dockerignore`, build context = repo root for all services
- [x] Physics: `MODEL_PATH` baked into image (ADR-004 amended)
- [x] Physics sidecar image (uv, URDF baked, no meshes)
- [x] Physics: `grpc_health.v1` healthcheck; `server` gates on `condition: service_healthy`
- [x] Sim server image (scratch-based, CGO-free, ADR-002); no healthcheck yet
- [x] TUI client image; `profiles:` + `docker compose run --rm tui` (PRD amended)
- [x] docker-compose.yml: drop `viz`, internal network, env-var addresses
- [x] Verified `docker compose up` + `docker compose run --rm tui`
- [x] Committed as per-slice commits, not one "containerize full stack"

## Phase 6: Dev Visualizer (Viser via Pinocchio; ADR-005 amended) (Complete)
- [x] Scaffold `viz/` as its own uv project
- [x] Implement gRPC state consumer (minimal, no reconnect handling)
- [x] Implement Viser rendering bridge
- [x] Address/rate CLI overrides (mirrors TUI's `resolveAddr()`)
- [x] Verify live arm state renders correctly, driven live via TUI commands
- [x] Committed as per-slice commits (not one "feat: add viser dev visualizer bridge")

## Phase 7: Integration and Polish
- [x] Full stack smoke test; fixed Dockerfile COPY layering and a stream double-close panic
- [ ] Write README.md (purpose, quickstart, architecture diagram)
- [ ] Write TUI unit tests — `internal/app` update() is pure; table-driven over
      mode switching, jog clamping, confirm expiry (today `go test ./tui/...`
      reports no test files)
- [ ] Record demo (gif or video)
- [ ] Commit: "docs: readme, architecture diagram, and demo"

## Phase 8: V2 Deployment (DevOps capstone or fast follow)
- [ ] Write fly.toml for server and physics apps
- [ ] Configure fly secrets for environment variables
- [ ] Set up GitHub Actions CI/CD
- [ ] Deploy to Fly.io, verify private network gRPC
- [ ] Update README with public demo URL

## Open TODOs
- [ ] Sidecar: pytest asserting INVALID_ARGUMENT for an UNSPECIFIED
      SetControlMode, so the rejection path can't rot
- [ ] TUI: absent/short `joint_target` or `cartesian_target` renders an in-pane
      diagnostic but is not validated — decide whether it is a protocol violation
- [x] Sidecar: gripper DOF free-spins (observed ~243 rad/s, q ~131k rad) — two
      defects behind one symptom, split below (ADR-020 context)
  - [x] Enforce joint limits in the plant per ADR-022
  - [x] Uniform viscous damping in the plant per ADR-023
- [ ] Sidecar: implicit damping term per ADR-023 deferral — removes the
      `d·dt/M < 2` bound and would admit physical STS3215 values
- [ ] Sidecar: finish lint/typecheck setup — ruff + pyright config (pyright
      `extraPaths` for the generated stubs) and a Makefile `lint` target
- [ ] Sidecar: clear the 48 existing ruff/pyright violations (chore, repo-wide)
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