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

for i in range(10):
    q = pin.randomConfiguration(model)
    M = pin.crba(model, data, q)
    print(f"--- q = {q}")
    print(f"   diag(M)")
    pretty_print_row(np.diag(M))

for i in range(10):
    q = pin.randomConfiguration(model)
    J = pin.computeFrameJacobian(model, data, q, gripper_frame_id, pin.LOCAL_WORLD_ALIGNED)
    # for now, task space control is positional control only (no attitude control)
    J_pos = J[:3]

    M_inv = pin.computeMinverse(model, data, q)
    A = J_pos @ M_inv @ J_pos.T
    Lambda = np.linalg.inv(A)
    lams = np.linalg.eigvals(Lambda)
    print(f"--- q = {q}")
    print("   eigen values of Lambda = inv(J_pos @ M_inv @ J_pos.T):")
    pretty_print_row(lams)