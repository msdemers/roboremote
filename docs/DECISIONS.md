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