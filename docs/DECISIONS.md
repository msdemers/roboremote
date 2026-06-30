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
  reused by command setpoints (e.g. `SetJointTarget`, feedforward torque).
- The EE pose type is named **`CartesianPose`** (position + quaternion) — not
  `Pose` (ambiguous with configuration `q`) nor `Transform` (implies a
  homogeneous matrix).
- Frames are **opaque positional vectors**; their meaning is supplied once by
  an **`ArmDescriptor` delivered as the first message of the `Subscribe`
  stream** (`oneof StreamFrame { descriptor | state }`) — consistency by
  construction, re-delivered on every reconnect. The descriptor carries joint
  names in model order, per-joint `q`/`v` start index and dimension (from
  Pinocchio's `idx_q`/`idx_v`/`nq`/`nv`), total `nq`/`nv`, limits, units, the
  EE frame name, and `model_name` + `model_version` (hash).
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