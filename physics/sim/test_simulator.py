from . import simulator, integrator
from control import controllers
from sim.status import ControlMode
from kinematics import forward
import numpy as np
import pinocchio as pin
import threading, time
from dataclasses import FrozenInstanceError
import pytest

class ConstantController:
    def __init__(self, tau, mode=ControlMode.UNSPECIFIED, target=None):
        self._tau, self.mode, self.target = tau, mode, target
    def compute(self, model, data, q, v):
        return self._tau

def test_clock(so101_model):
    model = so101_model
    dt = 0.001
    n_steps = 100
    sim = simulator.Simulator(model, dt, ConstantController(np.zeros(model.nv)))
    for _ in range(n_steps):
        sim.tick()
    assert abs(sim.t - n_steps*dt) < 1e-9, "simulator clock time does not match the numbers of sim step ticks"

def test_sim_matches_integrator(so101_model):
    model = so101_model
    dt = 0.001

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
    dt = 0.001
    n_steps = 1000

    sim = simulator.Simulator(model, dt, ConstantController(np.zeros(model.nv)))

    ee_pose_0 = forward.end_effector_pose(sim.model, sim.data, sim.q)

    for _ in range (n_steps):
        sim.tick()

    ee_pose_last = forward.end_effector_pose(sim.model, sim.data, sim.q)
    z_start = ee_pose_0.translation[2]
    z_end = ee_pose_last.translation[2]
    assert  z_end < z_start, f"final end effector height z = {z_end} should be lower than starting z = {z_start} after freefall"

def test_static_under_grav_comp_policy(so101_model):
    model = so101_model
    dt = 0.001
    n_steps = 1000

    sim = simulator.Simulator(model, dt, controllers.GravityCompensationController(), pin.randomConfiguration(model), np.zeros(model.nv))

    ee_pose_0 = forward.end_effector_pose(model, sim.data, sim.q)

    for _ in range(n_steps):
        sim.tick()

    ee_pose_last = forward.end_effector_pose(model, sim.data, sim.q)

    assert np.allclose(ee_pose_last.homogeneous, ee_pose_0.homogeneous, 0.0, 1e-9), "final pose should closely match initial pose under static gravity comp policy"

def test_run_stops(so101_model):
    model = so101_model
    dt = 0.001

    sim = simulator.Simulator(model, dt, controllers.GravityCompensationController())

    thread = threading.Thread(target=sim.run, daemon=True)
    thread.start()
    time.sleep(0.05)
    assert sim.t > 0, "sim time did not advance"

    sim.stop()
    thread.join(timeout=1.0) # wait an extra second to allow plenty of time for sim to stop
    assert not thread.is_alive()

def test_run_advances_realtime(so101_model):
    model = so101_model
    dt = 0.001

    sim = simulator.Simulator(model, dt, controllers.GravityCompensationController())

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
    dt = 0.001
    n_steps = 100

    sim = simulator.Simulator(model, dt, ConstantController(np.zeros(model.nv)))

    start_snapshot = sim.get_snapshot()

    for _ in range(n_steps):
        sim.tick()

    end_snapshot = sim.get_snapshot()
    
    assert end_snapshot.t == sim.t and np.array_equal(end_snapshot.q, sim.q) and np.array_equal(end_snapshot.v, sim.v) and np.array_equal(end_snapshot.tau, sim.tau), "latest snapshot did not match the final simulation data"
    
def test_snapshots_are_decoupled_from_state(so101_model):
    model = so101_model
    dt = 0.001

    sim = simulator.Simulator(model, dt, ConstantController(np.zeros(model.nv)))
    sim.tick()
    snapshot = sim.get_snapshot()
    sim.tick()
    assert snapshot.q[0] != sim.q[0], "snapshot decoupling failed: previous snapshot changed with simstate"
    
def test_snapshot_is_frozen(so101_model):
    model = so101_model
    dt = 0.001
    n_steps = 100

    sim = simulator.Simulator(model, dt, ConstantController(np.zeros(model.nv)))

    start_snapshot = sim.get_snapshot()
    with pytest.raises(FrozenInstanceError):
        start_snapshot.t = 0.3
