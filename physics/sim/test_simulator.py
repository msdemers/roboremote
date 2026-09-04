from . import simulator, integrator
from control import controllers
from dynamics.dynamics import compute_system_energy
from sim.status import ControlMode
from kinematics import forward
import numpy as np
import pinocchio as pin
import threading, time
from dataclasses import FrozenInstanceError
import pytest

DEFAULT_DT = 0.001 # seconds

class ConstantController:
    def __init__(self, tau, mode=ControlMode.UNSPECIFIED, target=None):
        self._tau, self.mode, self.target = tau, mode, target
    def compute(self, model, data, q, v):
        return self._tau

def test_clock(so101_model):
    model = so101_model
    dt = DEFAULT_DT
    n_steps = 100
    sim = simulator.Simulator(model, dt, ConstantController(np.zeros(model.nv)))
    for _ in range(n_steps):
        sim.tick()
    assert abs(sim.t - n_steps*dt) < 1e-9, "simulator clock time does not match the numbers of sim step ticks"

def test_sim_matches_integrator(so101_model):
    model = so101_model
    dt = DEFAULT_DT

    q_0 = pin.neutral(model)
    v_0 = np.zeros(model.nv)

    tau_c = 0.5*np.ones(model.nv)
    
    sim = simulator.Simulator(model, dt, ConstantController(tau_c), q_0, v_0)
    sim.tick()

    data = model.createData()

    q, v = integrator.step(model, data, q_0, v_0, tau_c, dt)

    assert np.allclose(sim.q, q, 0.0, 1e-9), f"simulated q = {sim.q} does not match integrated q = {q}"
    assert np.allclose(sim.v, v, 0.0, 1e-9), f"simulated v = {sim.v} does not match integrated v = {v}"

def test_free_fall_under_zero_tau(so101_model):
    model = so101_model
    n_steps = 1000

    sim = simulator.Simulator(model, DEFAULT_DT, ConstantController(np.zeros(model.nv)))

    ee_pose_0 = forward.end_effector_pose(sim.model, sim.data, sim.q)

    for _ in range (n_steps):
        sim.tick()

    ee_pose_last = forward.end_effector_pose(sim.model, sim.data, sim.q)
    z_start = ee_pose_0.translation[2]
    z_end = ee_pose_last.translation[2]
    assert  z_end < z_start, f"final end effector height z = {z_end} should be lower than starting z = {z_start} after freefall"

def test_static_under_grav_comp_policy(so101_model):
    model = so101_model
    n_steps = 1000

    sim = simulator.Simulator(model, DEFAULT_DT, controllers.GravityCompensationController(), pin.randomConfiguration(model), np.zeros(model.nv))

    ee_pose_0 = forward.end_effector_pose(model, sim.data, sim.q)

    for _ in range(n_steps):
        sim.tick()

    ee_pose_last = forward.end_effector_pose(model, sim.data, sim.q)

    assert np.allclose(ee_pose_last.homogeneous, ee_pose_0.homogeneous, 0.0, 1e-9), "final pose should closely match initial pose under static gravity comp policy"

def test_run_stops(so101_model):
    model = so101_model

    sim = simulator.Simulator(model, DEFAULT_DT, controllers.GravityCompensationController())

    thread = threading.Thread(target=sim.run, daemon=True)
    thread.start()
    time.sleep(0.05)
    assert sim.t > 0, "sim time did not advance"

    sim.stop()
    thread.join(timeout=1.0) # wait an extra second to allow plenty of time for sim to stop
    assert not thread.is_alive()

def test_run_advances_realtime(so101_model):
    model = so101_model

    sim = simulator.Simulator(model, DEFAULT_DT, controllers.GravityCompensationController())

    t_start = time.perf_counter()
    thread = threading.Thread(target=sim.run, daemon=True)
    thread.start()
    time.sleep(0.1)
    elapsed = time.perf_counter() - t_start
    sim.stop()
    thread.join(timeout=1.0)
    assert not thread.is_alive(), "sim thread should have stopped by now"
    assert np.allclose(sim.t, elapsed, rtol=0.2, atol=0.0), "sim time diverged from wall time"

def test_snapshot_returns_valid_data(so101_model):
    model = so101_model
    n_steps = 100

    sim = simulator.Simulator(model, DEFAULT_DT, ConstantController(np.zeros(model.nv)))

    start_snapshot = sim.get_snapshot()

    for _ in range(n_steps):
        sim.tick()

    end_snapshot = sim.get_snapshot()
    
    assert end_snapshot.t == sim.t and np.array_equal(end_snapshot.q, sim.q) and np.array_equal(end_snapshot.v, sim.v) and np.array_equal(end_snapshot.tau, sim.tau), "latest snapshot did not match the final simulation data"
    
def test_snapshots_are_decoupled_from_state(so101_model):
    model = so101_model

    sim = simulator.Simulator(model, DEFAULT_DT, ConstantController(np.zeros(model.nv)))
    sim.tick()
    snapshot = sim.get_snapshot()
    sim.tick()
    assert snapshot.q[0] != sim.q[0], "snapshot decoupling failed: previous snapshot changed with simstate"
    
def test_snapshot_is_frozen(so101_model):
    model = so101_model
    n_steps = 100

    sim = simulator.Simulator(model, DEFAULT_DT, ConstantController(np.zeros(model.nv)))

    start_snapshot = sim.get_snapshot()
    with pytest.raises(FrozenInstanceError):
        start_snapshot.t = 0.3

def test_sim_respects_joint_limits(so101_model):
    model: pin.Model = so101_model
    n_steps = 1000

    upper_limit_config = np.copy(model.upperPositionLimit)

    sim = simulator.Simulator(model, DEFAULT_DT, controllers.JointPdController(target=upper_limit_config+0.1), upper_limit_config-0.1, np.zeros(model.nv))

    for _ in range(n_steps):
        sim.tick()

    ee_pose_at_limit = forward.end_effector_pose(model, sim.data, upper_limit_config)
    ee_pose_last = sim.ee_pose

    assert np.allclose(ee_pose_last.homogeneous, ee_pose_at_limit.homogeneous, 0.0, 1e-9), "final pose should closely match pose at upper joint limit"

def test_sim_integration_damping_dissipates(so101_model):
    model: pin.Model = so101_model
    n_steps = 10000

    sim = simulator.Simulator(model, DEFAULT_DT, controllers.GravityCompensationController(), q0=model.lowerPositionLimit, v0=np.ones(model.nv)*np.pi/20.0)

    initial_ke = pin.computeKineticEnergy(sim.model, sim.data, sim.q, sim.v)

    for _ in range(n_steps):
        sim.tick()

    final_ke = pin.computeKineticEnergy(sim.model, sim.data, sim.q, sim.v)

    assert final_ke < initial_ke, "simulation system energy did not dissipate over time"

def test_closed_loop_response_is_bounded(so101_model):
    model: pin.Model = so101_model
    kp = controllers.VALIDATED_KP
    kd = controllers.VALIDATED_KD
    n_steps = 2000

    def lyapunov(v, e):
        return 0.5*v@v + 0.5*kp*e@e # v and e are 1-D arrays

    target = np.copy(model.upperPositionLimit) - 0.5
    sim = simulator.Simulator(model=model, dt=DEFAULT_DT, controller=controllers.JointPdController(target=target, kp=kp, kd=kd))

    V_0 = lyapunov(sim.v, sim.q-target)
    for _ in range(n_steps):
        sim.tick()
        assert np.min(model.upperPositionLimit - sim.q) > 0.0, "system hit a joint limit"
        assert lyapunov(sim.v, pin.difference(model, sim.q, target)) < V_0, "lyapunov function increased"
    
    assert np.max(np.abs(pin.difference(model, sim.q, target))) < 1e-3, "failed to converge to target"