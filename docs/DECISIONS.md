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
cleanly. Candidates evaluated: Pinocchio, PyBullet, MuJoC