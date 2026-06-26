from . import simulator, integrator
from control import controllers
from kinematics import forward
import numpy as np
import pinocchio as pin

def test_clock(so101_model):
    model = so101_model
    dt = 0.001
    n_steps = 100
    sim = simulator.Simulator(model, controllers.zero_control_policy, dt)
    for _ in range(n_steps):
        sim.tick()
    assert abs(sim.t - n_steps*dt) < 1e-9, "simulator clock time does not match the numbers of sim step ticks"

def test_sim_matches_integrator(so101_model):
    model = so101_model
    dt = 0.001

    q_0 = pin.neutral(model)
    v_0 = np.zeros(model.nv)
    
    def const_tau_policy(model, data, q, v):
        return 0.5*np.ones(model.nv)

    

    sim = simulator.Simulator(model, const_tau_policy, dt, q_0, v_0)
    sim.tick()

    data = model.createData()
    tau_c = const_tau_policy(model, data, q_0, v_0)

    q, v = integrator.step(model, data, q_0, v_0, tau_c, dt)

    assert np.allclose(sim.q, q, 0.0, 1e-9), f"simulated q = {sim.q} does not match integrated q = {q}"
    assert np.allclose(sim.v, v, 0.0, 1e-9), f"simulated v = {sim.v} does not match integrated v = {v}"

def test_free_fall_under_zero_tau(so101_model):
    model = so101_model
    dt = 0.001
    n_steps = 1000

    sim = simulator.Simulator(model, controllers.zero_control_policy, dt)

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

    sim = simulator.Simulator(model, controllers.gravity_compensation_policy, dt, pin.randomConfiguration(model), np.zeros(model.nv))

    ee_pose_0 = forward.end_effector_pose(model, sim.data, sim.q)

    for _ in range(n_steps):
        sim.tick()

    ee_pose_last = forward.end_effector_pose(model, sim.data, sim.q)

    assert np.allclose(ee_pose_last.homogeneous, ee_pose_0.homogeneous, 0.0, 1e-9), "final pose should closely match initial pose under static gravity comp policy"