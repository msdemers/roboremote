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

# q = pin.randomConfiguration(model)
q = pin.neutral(model)
print(f"q: {q.T}")

pin.forwardKinematics(model, data, q)
pin.updateFramePlacements(model, data)

print("====\njoints oMi[i].rotation\n====")
for i, name in enumerate(model.names):
    print(name, "\n", data.oMi[i].rotation) # joint orientation in world

print("====\njoint origins wrt parent (model.jointPlacements[i]\n====")
for i, name in enumerate(model.names):
    print(name, "\n", model.jointPlacements[i]) # fixed joint origins in their parents

print("====\n frame placements in parent joints (model.frames[i].placement)\n====")
for f in model.frames:
      print(f.name, "\n", f.placement)   # fixed offset of each frame vs its parent joint

print("joint positions in global frame:")
for name, oMi in zip(model.names, data.oMi):
    print("{:<24} : {: .2f} {: .2f} {: .2f}".format(name, *oMi.translation.T.flat))

print("frame positions in global frame:")
for name, oMf in zip(model.names, data.oMf):
    print("{:<24} : {: .2f} {: .2f} {: .2f}".format(name, *oMf.translation.T.flat))