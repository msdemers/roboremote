import pinocchio as pin

urdf_path = "../models/so101/so101_new_calib.urdf"
mesh_dir = "../models/so101/assets"

model = pin.buildModelFromUrdf(urdf_path)
print(f"Model name: {model.name}")
print(f"Number of joints: {model.njoints}")
print(f"Number of DOF: {model.nv}")
for i, name in enumerate(model.names):
    print(f"  joint {i}: {name}")

data = model.createData()

q = pin.randomConfiguration(model)
print(f"q: {q.T}")

pin.forwardKinematics(model, data, q)

for name, oMi in zip(model.names, data.oMi):
    print("{:<24} : {: .2f} {: .2f} {: .2f}".format(name, *oMi.translation.T.flat))