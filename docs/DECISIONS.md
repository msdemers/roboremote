# roboremote — Architecture Decision Records

---

## ADR-001: gRPC over WebSockets

**Status:** Accepted

**Context:**
The sim server must stream arm state to multiple clients in real time and
receive commands back. Two primary options: WebSockets (HTTP upgrade, ad hoc
JSON) or gRPC (HTTP/2, protobuf schema).

**Decision:**
Use gRPC with Protocol Buffers.

**Consequences:**
- Strongly typed interface contract via .proto file
- Bidirectional streaming is first-class (not hand-rolled)
- Go + gRPC is a natural pairing (both Google-origin)
- Aligns with ROS2/Isaac ecosystem philosophy
- Upfront cost: learn protobuf syntax and buf toolchain
- No native browser support (acceptable; browser client is not v1)

---

## ADR-002: Physics Sidecar Pattern

**Status:** Accepted

**Context:**
Physics engines (MuJoCo, Bullet, Pinocchio) have C/C++ dependencies that
break Go's static binary model (CGO_ENABLED=0). Embedding physics in the
Go server would produce large, complex containers and couple deployment
lifecycles.

**Decision:**
Run physics as a separate sidecar container. The Go sim server communicates
with it over gRPC on the Docker Compose internal network.

**Consequences:**
- Go sim server remains CGO-free, compiles to scratch-based container (~15MB)
- Physics engine choice is independently swappable
- Physics and server have independent deployment lifecycles
- Slight inter-process latency (sub-millisecond on local network, acceptable)
- Requires environment-variable-based address resolution for local/prod parity

---

## ADR-003: Pinocchio as V1 Physics Engine (MuJoCo as Fast Follow)

**Status:** Accepted

**Context:**
Physics sidecar requires a rigid body dynamics library that containerizes
cleanly. Candidates evaluated:

- **Pinocchio:** pure library, no renderer, pip installable, research-grade
  rigid body dynamics, excellent Python bindings, used heavily in academic
  robotics
- **PyBullet:** pip installable, headless via p.DIRECT, good URDF support,
  less accurate dynamics, maintenance slowing
- **MuJoCo:** pip installable (Python bindings), excellent dynamics and
  contact modeling, requires EGL/OSMesa for rendering (avoidable if
  rendering is handled by a separate client), DeepMind-maintained
- **Gazebo/ROS2:** deeply entangled with ROS middleware and display servers,
  images 3-5GB, not appropriate for a lightweight sidecar
- **NVIDIA Isaac:** requires NVIDIA Container Toolkit and GPU, not viable
  for a lightweight local sidecar

**Decision:**
Use Pinocchio for V1. Evaluate MuJoCo as a fast follow if contact dynamics,
tendon models, or broader ecosystem integration is needed.

**Consequences:**
- Containerizes in two lines: `FROM python:3.11-slim` + `pip install pin numpy`
- No rendering dependency -- visualization handled by separate Rerun client
- Research-grade dynamics accuracy appropriate for the domain
- Developer's PhD background in biomechanics simulation means Pinocchio's
  abstraction level (spatial algebra, Jacobians, mass matrices) is comfortable
- MuJoCo upgrade path is clean: MJCF model for SO101 already exists and is
  vetted

---

## ADR-004: SO-ARM100 / SO101 as V1 Robot Model

**Status:** Accepted

**Context:**
Project requires a real robot arm model with full inertial properties, mesh
assets, and joint definitions. Candidates considered included the UR5e
(industry standard, 6-DOF) and the SO-ARM100 / SO101 (open source, 5-DOF
+ gripper).

**Decision:**
Use the SO-ARM100 / SO101 (`so101_new_calib.urdf` and `so101_new_calib.xml`
as canonical URDF and MJCF respectively).

**Consequences:**
- URDF and MJCF both open source, community vetted, full inertial properties
  confirmed present
- STL mesh assets available for visualization
- Physical kit available for ~$100 -- real hardware follow-on is accessible
  to any user, not just well-funded labs
- Used as primary reference platform in Hugging Face LeRobot -- active
  community, abundant reference implementations
- 5-DOF + gripper is simpler than UR5e's 6-DOF, appropriate for V1 scope
- Models committed to `models/so101/`, mounted read-only into physics and
  viz containers via Docker Compose volume

---

## ADR-005: Rerun as Dev-Only Visualizer for V1 (Three.js for V2)

**Status:** Accepted

**Context:**
Validating physics sidecar output requires visual feedback during development.
A full interactive 3D visualizer with click-and-drag force application (tugging)
was originally scoped for V1. Candidates evaluated:

- **MeshCat:** Three.js wrapper, passive visualization, raycasting/interaction
  not supported natively, significant custom work required for tugging
- **Rerun:** time-series logging and visualization tool, excellent 3D rendering,
  Python SDK, used by LeRobot with SO101, passive/read-only, no tugging support
- **Three.js:** browser-based 3D, raycasting first-class, bidirectional via
  grpc-web, correct tool for interactive tugging, significant implementation work
- **Godot/Bevy:** game engines, natural raycasting, additional language required

**Decision:**
Use Rerun as a dev-only passive visualizer during V1 development. Defer
interactive 3D visualizer (Three.js) to V2. The TUI client is the sole
user-facing interaction mechanism for V1.

**Consequences:**
- Rerun bridge is ~100 lines of Python, negligible implementation cost
- Immediate visual validation of physics sidecar output during development
- Rerun is not part of the end-user Docker Compose stack -- dev tool only
- Interactive tugging deferred to V2 as a separate, properly scoped product
- V1 capstone story is cleaner: containerized real-time gRPC sim with Go TUI
- V2 Three.js visualizer becomes its own compelling portfolio piece

---

## ADR-006: Docker Compose for V1, Fly.io for V2

**Status:** Accepted

**Context:**
Project requires a deployment strategy that supports local development for
V1 and public cloud hosting for V2. Hosting candidates evaluated: Fly.io,
Railway, Render, AWS, CoreWeave.

**Decision:**
Use Docker Compose for V1 local orchestration. Target Fly.io for V2 cloud
deployment using two separate Fly apps (sim server and physics sidecar)
communicating over Fly.io's private WireGuard network.

**Consequences:**
- `docker compose up` is the single command to run the full V1 stack locally
- All service addresses are environment-variable-based from day one for
  local/prod parity
- Go sim server compiles to a scratch-based container (~15MB), ideal for Fly.io
- Fly.io chosen over Railway/Render for persistent process support, native
  gRPC/HTTP2, Go ecosystem alignment, and global edge deployment
- Fly.io has no GPU support -- future GPU workloads (Isaac, policy training)
  will require a separate provider (AWS or CoreWeave, decision deferred)
- V2 deployment stubs committed to `deploy/` directory with documented
  `fly.toml.example` files per service
- V2 deployment targeted as DevOps capstone project or immediate fast follow

---

## ADR-007: Physics Sidecar Owns the Integration Clock

**Status:** Accepted

**Context:**
ADR-002 established the physics sidecar pattern but left the sim loop's
ownership ambiguous: PLAN Phase 3 lists a "fixed-step integrator" in Python
while Phase 4 lists a "simulation loop goroutine" in Go. Both cannot own the
timestep. If the Go server ticks the clock and calls Python per-step over
gRPC, a network hop sits inside the integration loop — at hundreds of Hz the
sim rate becomes hostage to RPC jitter, undercutting ADR-002's
"sub-millisecond, acceptable" assumption.

**Decision:**
The Python physics sidecar owns the integration clock. It runs the fixed-step
integrator and streams resulting state outward. The Go sim server is a pure
fan-out relay: it subscribes to sidecar state, broadcasts to N clients, and
routes inbound commands back to the sidecar. It does not advance sim time.

**Consequences:**
- No network hop inside the integration loop; sim rate is set by the sidecar,
  not by RPC timing.
- Go server stays a stateless relay — simpler, easier to scale fan-out.
- The Phase 4 "simulation loop goroutine" is really a stream pump, not an
  integrator; PLAN wording should be read in that light.
- Determinism and timestep discipline live in one place (Python), aligning
  with the developer's numerics background.
- The sidecar must drive its own loop independent of client connections
  (the sim advances whether or not anyone is watching).

---

## ADR-008: Client Transport — Server-Streaming State + Unary Commands

**Status:** Accepted

**Context:**
The original proto sketched a single bidirectional `ArmSimService.SimStream`
carrying commands up and state down, alongside redundant unary `GetArmState`
and `SetControlMode` RPCs. The bidi mashup conflated three distinct flows
(state out, commands in, sensor lifecycle) and gave commands no
acknowledgement — a command vanished into the stream, and gRPC status codes
only fire on stream teardown, not per-message. It also forced one contract
across two asymmetric hops (sidecar↔server vs server↔client).

**Decision:**
Decompose the client-facing interface into two RPC shapes:
- One **server-streaming** RPC for state:
  `Subscribe(SubscribeRequest) returns (stream StreamFrame)`.
- A set of **unary** command RPCs, each returning a response message carrying
  accept/reject status. Locked so far: `ResetConfiguration` (snap),
  `SetJointTarget` (servo), `SetControlMode`. Remaining command roster
  (Cartesian target, sensor add/remove, control-mode representation, sensor
  ownership) is still being designed and will be recorded separately.

The bidirectional `SimStream` is removed.

**Consequences:**
- Unary commands restore per-command ack/nack semantics for free (each has a
  response message).
- State is a clean one→many server stream; per-client rate selection lives in
  the request (see ADR-009).
- Simpler reconnection and error handling than bidi.
- The command set extends without touching the state stream.
- Consistent with ADR-007: the Go server stays a pure relay.

---

## ADR-009: Sidecar Publish Cadence and Per-Client Decimation

**Status:** Accepted (extends ADR-007)

**Context:**
ADR-007 placed the integration clock in the sidecar but left open the rate at
which state reaches clients and where rate decoupling lives. A server-pull
model reintroduces RPC timing into cadence; locking clients to the integration
tick (≈1 kHz) is wasteful and unrenderable.

**Decision:**
The sidecar **pushes** state outward at a fixed **120 Hz** publish rate,
decoupled from its integration tick via a latest-snapshot slot (integrate
fast, publish at 120 Hz). The Go server is a pure fan-out relay and
**decimates per subscriber** to a client-selected rate from a fixed menu
`{120, 60, 30} Hz` (decimation factor N = 1/2/4). Rate is selected via a
`StreamRate` enum in the `Subscribe` request.

**Consequences:**
- No network hop inside the integration loop (preserves ADR-007); cadence is
  owned by the sidecar.
- Decimation only drops frames, never invents them: client rate ≤ publish
  rate, and only integer divisors are offered — no temporal aliasing/beating.
- The `StreamRate` enum makes invalid rates unrepresentable by construction.
- Latest-value-wins semantics: a slow or stalled consumer never accrues a
  backlog.
- 120 Hz anchors to the 60 Hz monitor family for the future visualizer; the
  TUI needs only 30/60.

---

## ADR-010: On-the-Wire State Representation

**Status:** Accepted

**Context:**
The original proto modeled state as `repeated JointState{name, position,
velocity, effort}`, re-transmitting joint-name strings for every joint on
every frame and forcing clients to string-match to align state. This
mismatches how dynamics systems represent state (generalized vectors) and how
the sidecar's `SimSnapshot{t, q, v, tau}` is already shaped.

**Decision:**
- `ArmState` carries **generalized vectors**: `Coordinates q`, `Velocities v`,
  `Actuation tau`, plus `CartesianPose end_effector` (FK of the
  `gripper_frame_link` frame), `sim_time`, and `ArmStatus`. The gripper is a
  DOF *inside* `q`, not a separate field; the end-effector is a kinematic
  *frame* whose pose is computed by FK, not a coordinate.
- `Coordinates` / `Velocities` / `Actuation` are **shared message types**,
  reused by command setpoints (`SetTarget`; see ADR-013).
- The EE pose type is named **`CartesianPose`** (position + quaternion) — not
  `Pose` (ambiguous with configuration `q`) nor `Transform` (implies a
  homogeneous matrix).
- Frames are **opaque positional vectors**; their meaning is supplied once by
  a **`ModelDescriptor` delivered as the first message of the `Subscribe`
  stream** (`StreamEnvelope { oneof payload: descriptor | state }`) —
  consistency by construction, re-delivered on every reconnect. The descriptor
  carries total `nq`/`nv` plus a `repeated JointInfo`, each with joint name,
  `JointType`, per-joint `nq`/`nv`, start indices (Pinocchio's
  `idx_q`/`idx_v`), position/velocity/effort limits, and tree topology
  (`id`/`parent_id` for per-joint TUI), plus `model_name` + `model_version`
  (hash). Units are conveyed by `JointType` (revolute→rad, prismatic→m), not an
  explicit units field. Final message names finalized in ADR-015.
- **Model geometry/meshes are NOT shipped over gRPC.** Clients load them
  out-of-band (volume mount per ADR-004) and verify against
  `model_name`/`model_version`. Asset distribution for genuinely remote
  clients is deferred to V2.

**Consequences:**
- Wire shape mirrors the sidecar's snapshot and Pinocchio's `nq`/`nv`; no
  per-frame strings, alignment is positional.
- Shared vector types keep state and command messages symmetric.
- Descriptor-first guarantees a client can never decode a frame without first
  holding the key; the Go TUI (no URDF parser) depends on it entirely.
- The authoritative `q`-vector layout comes from the sidecar, so client
  correctness never rests on "did you parse the URDF the same way I did."
- Separates three concerns that "the model" had been conflating:
  state-decoding metadata, kinematic model, and visual geometry.
- Rigor via verifiable consistency (`model_name`/hash), not by streaming bytes
  on the hot path.

---

## ADR-011: Quaternion Ordering — Scalar-Last (x, y, z, w)

**Status:** Accepted

**Context:**
`CartesianPose` carries orientation as a quaternion; the wire order must be
fixed. The industry is split: Pinocchio/Eigen/ROS tf2 use scalar-last
`{x, y, z, w}`; MuJoCo and NVIDIA Isaac use scalar-first `{w, x, y, z}`. The
original `Pose` sketch listed `qw` first.

**Decision:**
Use **scalar-last `{x, y, z, w}`**, Hamilton convention (right-handed). A
survey of robotics/sim tooling found scalar-last to be the majority; it also
matches Pinocchio/Eigen's own internal coefficient order, minimizing
conversion in the sidecar's `SE3→CartesianPose` helper.

**Consequences:**
- The sidecar's `SE3→CartesianPose` helper is a near-direct copy of the Eigen
  quaternion coefficients.
- The MuJoCo fast-follow (ADR-003) uses scalar-first `wxyz`; that conversion
  lives solely in the `SE3→CartesianPose` helper at the engine boundary, never
  on the wire.
- Resolves the PLAN open TODO on quaternion conventions.

---

## ADR-012: V1 Interaction Scope — Sensor Nodes Deferred, Last-Writer-Wins

**Status:** Accepted

**Context:**
User-placeable sensor nodes (position/attitude/velocity probes) were the
largest remaining source of v1 complexity: shared mutable cross-client state,
add/remove lifecycle RPCs, and physics-side world-pose/velocity computation per
node. V1's thesis — real-time gRPC state streaming with multi-client fan-out
and command routing — does not depend on them.

**Decision:**
Defer user-configurable sensor nodes to V2. V1 client interaction is: switch
control policy, set a joint-space (`Coordinates`) target, set a task-space
(`CartesianPose`) target, snap to a reference config (`ResetConfiguration`),
and observe `q`/`v`/`tau`/EE state. Mode and target are shared sim state with
**last-writer-wins** semantics — no per-client ownership or locking.

**Consequences:**
- Proto drops `SensorNode`, `SensorNodeState`, the `add_sensor`/`remove_sensor`
  `oneof` arms, and `sensor_nodes` from the stream. (`Wrench`/`ExternalWrench`
  tugging already V2 per ADR-005.)
- Client interface = `Subscribe` (state) + unary `SetControlMode`,
  `SetTarget`, `ResetConfiguration` (target RPCs collapsed per ADR-013).
- No cross-client mutable-collection concurrency in v1; conflicting commands
  resolve last-writer-wins.
- PRD success criteria and PLAN Phases 3–5 updated to remove sensor work.

---

## ADR-013: Control Modes and Targeting

**Status:** Accepted

**Context:**
V1 has five control policies, each admitting exactly one target kind (none /
joint / Cartesian). The raw-vs-compensated split means a target cannot
disambiguate the mode (a `CartesianPose` target fits both Task-PD-Raw and
Task-PD-Compensated).

**Decision:**
- `ControlMode` is a flat enum of five (+ `UNSPECIFIED`): `GRAVITY_COMP` (no
  target), `JOINT_PD_RAW`, `JOINT_PD_COMPENSATED` (both `Coordinates`),
  `TASK_PD_RAW`, `TASK_PD_COMPENSATED` (both `CartesianPose`).
- Mode is always set explicitly via `SetControlMode`; never inferred from a
  target.
- A single `SetTarget(oneof { Coordinates joint; CartesianPose cartesian })`
  replaces separate joint/Cartesian target RPCs. The server rejects a target
  whose `oneof` arm doesn't match the active mode.
- On mode entry the setpoint defaults to **current state** (joint target =
  current `q`; Cartesian target = current EE pose) — bumpless transfer, no
  commanded jump. `SetTarget` overrides afterward.

**Consequences:**
- Command roster: `Subscribe` + unary `SetControlMode`, `SetTarget`,
  `ResetConfiguration`.
- Invalid mode/target combinations resolve at a single rejection point
  (`SetTarget` vs active mode).
- Mode switches are always safe regardless of client timing.
- Supersedes the `SetJointTarget`/`SetCartesianTarget` split in ADR-012.
- Clarified by ADR-019: "compensated" means *full inverse-dynamics*
  compensation (Coriolis + gravity via computed torque), not gravity-only.

---

## ADR-014: Sidecar↔Server Shares One Service; Server Proxies

**Status:** Accepted

**Context:**
Two gRPC hops exist: client↔server and server↔sidecar. Command payloads are
identical across them (ADR-007 makes the server a pure relay), so the question
is one shared service definition vs two sharing message types.

**Decision:**
One shared service (`ArmSimService`), shared messages across both hops. The
**sidecar is the authoritative implementor** — it owns `q`/mode/controllers,
validates, and originates acks. The server implements the same interface:
- **Unary commands** (`SetControlMode`, `SetTarget`, `ResetConfiguration`):
  verbatim forward to the sidecar; ack returned unchanged.
- **State `Subscribe`:** *not* a transparent forward. The server holds a single
  full-rate (120 Hz) upstream subscription to the sidecar and fans out,
  decimating per client via `StreamRate` (ADR-009). The server requests 120 Hz
  upstream; client-rate selection is a server-side concern.

**Consequences:**
- The relay is a trivial forwarder for the three command RPCs.
- The only non-trivial relay logic is state fan-out/decimation — inherent, not
  avoidable.
- Validation, authority, and acks live solely in the sidecar (ADR-007).
- One service def + shared messages = no payload duplication; a client sees an
  identical interface whether it talks to the sidecar or the server.

---

## ADR-015: Proto Finalization — Naming and Error Model

**Status:** Accepted

**Context:**
ADR-008/010 were written before the proto was authored; the built file settled
some names and an error model those ADRs left loose. Recorded here as the
authoritative surface.

**Decision:**
- **Names:** the stream-wrapper type is `StreamEnvelope` (a `oneof payload` of
  `ModelDescriptor` | `ArmState`), not `StreamFrame`; the descriptor is
  `ModelDescriptor`, not `ArmDescriptor`. Per-joint metadata is `JointInfo`
  with a nested `JointType` enum.
- **Errors via gRPC status codes, not payload fields.** Command RPCs signal
  rejection with a non-OK status (e.g. `INVALID_ARGUMENT` for a target whose
  `oneof` arm mismatches the active mode), raised in the handler — not a
  `bool success` / `string message` body. This uses gRPC's out-of-band status
  channel instead of reinventing it.
- **Dedicated empty response messages** (`SetControlModeResponse` {},
  `SetTargetResponse` {}, `ResetConfigurationResponse` {}), not
  `google.protobuf.Empty` — so a field can be added later without breaking the
  RPC signature (Google API guidance). Success carries no payload today because
  the stream already echoes `active_mode`/`active_target`.
- **`StreamRate`** values are `STREAM_RATE_{UNSPECIFIED,30,60,120}`;
  `UNSPECIFIED` resolves to 60 Hz **in the server handler**, not via the proto
  zero value (keeps zero-as-sentinel discipline).
- **`ResetConfiguration`** resets to the model's canonical configuration via
  `pin.neutral(model)` (correct on the manifold for any joint types), not
  literal zeros; request is empty.
- Enum values are prefixed with their UPPER_SNAKE enum name
  (`STREAM_RATE_`, `JOINT_TYPE_`, `ARM_STATUS_`, `CONTROL_MODE_`) — proto3 enum
  values leak into the enclosing namespace, so the prefix prevents collisions.

**Consequences:**
- Clients handle command failure in their error path, not by branching on a
  body flag.
- `buf lint` (STANDARD) passes; the one excepted rule is
  `RPC_RESPONSE_STANDARD_NAME` (Subscribe returns `StreamEnvelope`, not
  `SubscribeResponse` — an intentional, meaningful name for a streaming
  oneof wrapper).
- Supersedes the `StreamFrame`/`ArmDescriptor` names in ADR-008/010.

---

## ADR-016: buf Tooling Layout and Dual Codegen

**Status:** Accepted

**Context:**
The repo is not a monorepo but a set of self-contained services
(`physics/`, `server/`, `tui/`), each owning its own build config
(`pyproject.toml`, `go.mod`). buf config and generated stubs must fit that
convention and serve both Go and Python consumers.

**Decision:**
- buf v2, **single module**, config co-located in `proto/` (`proto/buf.yaml`,
  `proto/buf.gen.yaml`), mirroring the per-component config-ownership
  convention. The deprecated v1 `buf.work.yaml` is removed; no root buf config.
- **Dual codegen:** `buf generate` emits **Go only** (`protoc-gen-go`,
  `protoc-gen-go-grpc`). **Python** is generated separately via
  `grpc_tools.protoc` run inside `physics/`'s uv env, so stub versions match
  the pinned `grpcio` runtime in the sidecar.
- **`make proto` is the single full-regen entry point** (lint → Go gen →
  Python gen). Running bare `buf generate` regenerates only Go and leaves
  Python stubs stale.

**Consequences:**
- Config lives beside the protos it governs; run buf from `proto/` (or via
  `make proto`, which `cd`s in).
- Config-internal paths are cwd-relative, so `buf.gen.yaml` uses proto-local
  paths (`directory: .`, `out: gen/go`).
- Python stub/runtime version parity is guaranteed at the cost of two codegen
  tools rather than one.

---

## ADR-017: Generated-Code Distribution Across Polyglot Services

**Status:** Accepted (interim); Go durable step complete, Python durable step
still deferred to Phase 3

**Context:**
Generated stubs live at `proto/gen/{go,python}` — a sibling of `physics/`,
`server/`, `tui/`. That location sits **outside** every service's source
directory, every service's Docker **build context** (`build: ./physics` can't
reach `../proto`), and every Go **module** boundary. The Python stubs use
namespace packages (no `__init__.py`), so `import roboremote.arm.v1.arm_pb2`
resolves only when `proto/gen/python` is on `sys.path`. Two distinct problems
follow, and they are **not** the same fix:
- **Local:** purely a `sys.path` issue.
- **Container:** the stubs aren't even in the image — the build context can't
  see them — *before* any path concern applies.

**Decision:**
- **Interim (v1 local dev):** make `proto/gen/python` importable via one
  central, checked-in mechanism per entry point — `pytest` `pythonpath` for
  tests, and a `make run-physics` target that sets `PYTHONPATH=../proto/gen/python`
  for the server. No ad-hoc per-invocation `PYTHONPATH` scattered in docs/shells.
- **Durable (deferred to Phase 3 / containerization):** package the generated
  protos as an installable dependency (`roboremote-proto`) that each Python
  service depends on, and set the Docker build context to the repo root (or
  install a pre-built wheel) so images contain the stubs. The Go side has the
  identical shape — resolve `proto/gen/go` across the separate `server`/`tui`
  modules via a `go.work` or a dedicated module.

**Consequences:**
- Local dev (tests + server + smoke client) unblocked now without spreading a
  fragile one-liner.
- The container gap is a known, bounded change scoped to Phase 3, where the
  compose/Dockerfiles are edited anyway — not a lurking unknown.
- Distribution strategy is recorded, so it isn't rediscovered per service.
- The Go durable step landed early: `tui` joined the root `go.work` during its own
  setup (Phase 5), not held for the batched containerization pass — no `replace`
  directives or version pins needed between `proto/gen/go`, `server`, and `tui`.

---

## ADR-018: Setpoint Smoothing Is Out of Scope for the Sidecar

**Status:** Accepted

**Context:**
A mid-mode `SetTarget` steps the setpoint, and thus commanded torque. Smoothing
goal→command would avoid the jerk, but it needs its own tick-evolving state and
is a higher-level control concern (trajectory generation, optimal/agentic
policy) — not physics.

**Decision:**
The sidecar stays physics-only: `(q, v, setpoint) → tau`. It holds a single
target (goal == commanded setpoint); `SetTarget` writes it directly. Reference
shaping / trajectory smoothing is deferred to a future control layer above the
sidecar.

**Consequences:**
- One `active_target` field, no evolving second state; wire and snapshot keep a
  single setpoint.
- Setpoint step changes (and resulting torque steps) are the caller's concern.
- Preserves the pure `state → tau` policy shape.

---

## ADR-019: Control Laws — Computed-Torque and Inertia-Weighted PD

**Status:** Accepted

**Context:**
Fixed PD gains in torque space (`τ = kp·e − kd·v`) are scaled per-joint by
`M⁻¹`, so a gain safe on one joint is unstable on another. At `dt=1ms` the
lightest joint (gripper) diverged to NaN within a few ticks.

**Decision:**
Both joint controllers command a desired acceleration
`a_des = kp·e − kd·v` (`e = pin.difference(q, target)`) and map it to torque
via Pinocchio inverse-dynamics recursions:
- **JOINT_PD_COMPENSATED** — computed torque:
  `τ = rnea(q, v, a_des) = M·a_des + C·v + g`. Feedback-linearizes to
  `ë + kd·ė + kp·e = 0`.
- **JOINT_PD_RAW** — inertia-weighted PD, no bias comp:
  `τ = rnea(q,v,a_des) − nonLinearEffects(q,v) = M·a_des`. Stable but droops
  under gravity.

`nonLinearEffects` (`C·v + g`) is exactly the difference: COMPENSATED = RAW + bias.

**Consequences:**
- Gains are inertia-independent — one scalar pair works for all joints and both
  laws. `kp = ωn²`, `kd = 2ζωn`; chosen `ωn=50, ζ=1` (`ωn·dt=0.05 ≪ 2`).
- No dense `M` formed — O(n) recursions, sidesteps `crba`'s upper-triangular
  symmetrization.
- RAW vs COMPENSATED is principled: uniform stability from M-weighting (both),
  position-holding from bias cancellation (COMPENSATED only).
- Task-space (`TASK_PD_*`) will need `crba`/operational-space inertia; deferred.

---

## ADR-020: Task-Space Control — Position-Only Operational Space (V1)

**Status:** Accepted (RAW verified live; COMPENSATED designed, implementation pending)

**Context:**
SO101 is 5-DOF + gripper (`nq=6`). The gripper's EE-frame Jacobian column is
*identically zero* (verified across random configs), so the frame Jacobian is
rank ≤ 5 and `J M⁻¹ Jᵀ` is singular for a full 6-D pose task — arbitrary SE(3)
is unreachable. Joints 2–4 are parallel-axis, adding internal singularities.
The arm also has genuine 2-DOF redundancy for a 3-D task.

**Decision:**
- **Position-only, 3-DOF task** for V1 (Euclidean error, no SO(3)). Orientation
  deferred to a specific workspace need.
- **Operational space (Khatib), `τ = JᵀF + τ_null (+ b)`:**
  - RAW: `F = Λ·a_x`, `τ = JᵀF + τ_null` — op-space-inertia-weighted, no bias
    (droops under gravity).
  - COMPENSATED: inverse-dynamics OSC — `F = Λ·(a_x − J̇v)`,
    `τ = JᵀF + τ_null + b` with `b = nle = C·v + g`. Cancels the bias *directly
    in joint space* rather than projecting it through task space (the equivalent
    Khatib form `F = Λ(a_x − J̇v + J M⁻¹·nle)`, `τ = JᵀF`). Same task result
    `ẍ = a_x`, but this variant also compensates **null-space and gripper**
    gravity/Coriolis (no null-space droop; the jaw gravity-holds) and avoids the
    `J M⁻¹·nle` round-trip projection.
  - `a_x = kp·e_x − kd·ẋ`, `Λ = (J_pos M⁻¹ J_posᵀ + λ²I)⁻¹`.
- **Constant Tikhonov damping** `λ` for singularity robustness.
- **Redundancy via null-space damping only:** `τ_null = N(−kn·v)`,
  `N = I − Jᵀ(Λ J M⁻¹)`.
- **Gripper decoupled from `τ_null`** (zero row + column of `N` for the gripper
  DOF): its zero task-Jacobian + lightest inertia would otherwise dominate the
  `kn·dt/M < 2` stability bound; `kn` is now bounded by the lightest *arm* joint.
- **Gains (provisional):** `kp=2500, kd=100` (`ωn=50, ζ=1`, transfer directly via
  unit-mass decoupling); `λ=0.3`; `kn≈0.015`.

**Consequences / deferred:**
- One gain set serves RAW and COMPENSATED (unit-mass decoupling).
- Deferred: full-pose/orientation control; **variable damping `λ(σ_min)`**
  (Nakamura/Wampler, activates only near singularities); null-space posture task;
  inertia-weighted null-space damping; gripper as a real open/close actuator.
- Gains are hardcoded defaults; a tuning/config surface is future work.

---

## ADR-021: TUI Interaction Architecture — Paged Layout, Jog Control, Command Pump

**Status:** Accepted; amended 2026-08-05 (modal confirm surface, key ownership)

**Context:**
Phase 5's remaining scope turns the TUI from passive monitor into command
surface (mode switching, target entry per ADR-012/013). Open questions: layout
paradigm (dashboard vs full-screen views vs popups), keyboard regimes for a
screen repainting at 30 Hz, target entry UX, what the operator sees while
commanding, how rejections surface, and how a burst of commands stays ordered
over one gRPC conn.

**Decision:**
- **Paged layout with persistent chrome**, not a packed dashboard: fixed
  header, tab bar, and footer frame a content region that renders exactly one
  **page** at a time (Monitor, Control, future views). The active page owns
  the content region and all non-global keys (explicit modal regimes, no
  widget-focus ambiguity). Vocabulary: "page" — content occupying a region
  exclusively, selected by tab; not "pane" (implies simultaneous siblings) or
  "screen" (implies full-terminal). Deliberate side effect: one binary
  composes a multi-terminal dashboard — one terminal on Monitor, another on
  Control — which live-demos the multi-client fan-out thesis and
  last-writer-wins semantics.
- **Control page shows sim truth while commanding:** active mode, commanded
  target, current state, error (per-DOF `q_err` in joint modes; 3-vector +
  norm in task modes), tau, plus a compact `q / v / tau / EE` strip (Monitor's
  rich table makes that strip redundant there — it is Control-page content,
  not chrome). `GRAVITY_COMP` renders an explicit no-target state (`—`), never
  zeros. All values come from the stream's echoed `active_mode`/`active_target`
  — the page reflects the sim, not the client's last send.
- **Persistent footer is chrome, state-free:** global key hints plus a command
  status line (`✓` fades; `✗ code — message` sticky until the next command).
  Rejections render the gRPC status verbatim — no client-side error taxonomy
  for five commands with one rejection point.
- **Target entry is jog-first:** select DOF/axis, step keys send absolute
  `SetTarget` immediately (teleop feel; step-bounded commands by construction).
  Vocabulary split: **jog** = continuous control verb (immediate), **go-to** =
  discrete command verb (typed value, confirm, dispatch) — deferred, slots in
  later without redesign.
- **Local jog cursor with resync:** each press increments a client-side cursor
  (correct stacking during bursts; echoed base would drop increments to
  staleness) and sends absolute. The cursor carries a whole target vector —
  `SetTargetRequest` has no partial form. It resyncs to the echoed
  `active_target` whenever jogging is idle, which is also how it initializes:
  honest convergence to sim truth, adopts other writers' targets.
- **Mode keys immediate, arm-moving keys confirmed:** number keys switch mode
  with no confirm — ADR-013's bumpless transfer makes switching always safe,
  and a dialog would re-litigate that server-side guarantee. Active-mode
  highlight follows the echoed stream, not the keypress. `ResetConfiguration`
  gets a confirm step: it is go-to-shaped — the one key that moves the arm.
- **Confirms are a modal overlay** (amended): a centered dialog composed over
  the finished view, capturing all keys while pending. The footer already
  carries command status, and deferred go-to entry is the same shape — the
  overlay is a surface both use, not machinery for one keystroke. `q` (quit)
  takes the same treatment; `ctrl+c` stays unconditional.
- **Key ownership follows blast radius** (amended): global keys act on the
  client (`q`, `tab`), page keys act on the arm. `r` is therefore a
  Control-page key, preserving Monitor as a genuinely read-only observer — a
  property the two-terminal fan-out demo depends on.
- **Single gRPC edge + command pump:** `internal/stream` grows into the sole
  owner of the `ClientConn` (stream out, unary in). Commands dispatch through
  one serialized pump goroutine (next send after previous ack) with a
  **depth-1 latest-wins slot for `SetTarget`** — jog bursts coalesce to the
  newest target; mode/reset pass through unslotted (never coalesced). Fixes
  the real hazard that concurrent unary RPCs on one conn have no ordering
  guarantee (a burst's second-to-last press could land last and win).

**Consequences:**
- Pages render only the content region; the root `View()` owns chrome and
  layout arithmetic (content height = terminal − header − tab bar − footer).
  Pages own only state they alone mutate; sim truth lives once on the root and
  is passed in — no second copy to go stale.
- The PLAN "control input monitor panel" is not a third panel: it is the
  Control page's state strip.
- Latest-value-wins now appears at all three tiers — sidecar snapshot slot,
  relay per-subscriber slots, TUI command slot.
- Known race accepted: mid-jog mode change from another client draws an
  `INVALID_ARGUMENT` rejection → footer shows it, jog stops, cursor and mode
  resync from the stream.
- Rate limiting of jog RPCs falls out of pump serialization + coalescing; no
  explicit throttle needed.
- Three text surfaces with distinct ownership: footer = global hints + command
  status, page hint row = that page's keys, overlay = confirms.