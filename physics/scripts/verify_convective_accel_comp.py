import pinocchio as pin
import numpy as np

urdf_path = "../models/so101/so101_new_calib.urdf"
mesh_dir = "../models/so101/assets"
end_effector_frame = "gripper_frame_link"

def pretty_print_row(row_vec, sig_figs=4, width=12):
    formatted_row = [f"{item:> {width}.{sig_figs}g}" for item in row_vec]
    print(" ".join(formatted_row))

def pretty_print_matrix(matrix, sig_figs=4, width=12):
    """
    Prints a 2D NumPy array to the terminal in a clean grid layout.
    Maintains specific significant figures and aligns columns.
    """
    for row in matrix:
        # Format every item in the row into a fixed-width string
        pretty_print_row(row_vec, sig_figs, width)

model: pin.Model = pin.buildModelFromUrdf(urdf_path)
print(f"Model name: {model.name}")
print(f"Number of coordinates: {model.nq}")
print(f"Number of DOF: {model.nv}")

data = model.createData()
gripper_frame_id = model.getFrameId(end_effector_frame)

v = np.zeros(model.nv)

for i in range(10):
    q = pin.randomConfiguration(model)
    J = pin.computeFrameJacobian(model, data, q, gripper_frame_id, pin.LOCAL_WORLD_ALIGNED)
    #ee_translation = forward.end_effector_pose(model, data, q).translation
    M_inv = pin.computeMinverse(model, data, q)
    # compute d(J)/dt * v (Convective Acceleration)
    pin.forwardKinematics(model, data, q, v, np.zeros(model.nv)) # zero out accel effect from dd(q)/dtt
    dJv = pin.getFrameClassicalAcceleration(model, data, gripper_frame_id, pin.LOCAL_WORLD_ALIGNED).linear

    print(f"--- q = {q}")
    print("   convective accel d(J)dt * v when v = 0:")
    pretty_print_row(dJv)
