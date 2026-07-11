import pinocchio as pin
import numpy as np

urdf_path = "../models/so101/so101_new_calib.urdf"
mesh_dir = "../models/so101/assets"
end_effector_frame = "gripper_frame_link"

def pretty_print(matrix, sig_figs=4, width=12):
    """
    Prints a 2D NumPy array to the terminal in a clean grid layout.
    Maintains specific significant figures and aligns columns.
    """
    for row in matrix:
        # Format every item in the row into a fixed-width string
        formatted_row = [f"{item:> {width}.{sig_figs}g}" for item in row]
        # Join elements with a space and print without brackets
        print(" ".join(formatted_row))

model: pin.Model = pin.buildModelFromUrdf(urdf_path)
print(f"Model name: {model.name}")
print(f"Number of coordinates: {model.nq}")
print(f"Number of DOF: {model.nv}")

data = model.createData()

for i in range(5):
    q = pin.randomConfiguration(model)
    gripper_frame_id = model.getFrameId(end_effector_frame)
    J = pin.computeFrameJacobian(model, data, q, gripper_frame_id)
    print(f"--- Jacobian at q = {q}")
    pretty_print(J, 4, 12)
    M_inv = pin.computeMinverse(model, data, q)
    print(f"--- inverse(Mass) at q = {q}")
    pretty_print(M_inv, 4, 12)
    
