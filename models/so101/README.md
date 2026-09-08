# SO-101 - URDF and mesh assets

A vendored copy of the SO-101 manipulator model description files (URDF + STL meshes) from [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100/).

## Provenance

This directory contains a subset of model assets published in the [SO-ARM100 repository](https://github.com/TheRobotStudio/SO-ARM100/) under the Apache-2.0 license. The URDF and mesh files in `roboremote` are byte-identical copies of the originals at [Simulation/SO101](https://github.com/TheRobotStudio/SO-ARM100/tree/main/Simulation/SO101) (verified 2026-09-08, upstream `Simulation/SO101` at `f555c6c`). This directory retains only the files `roboremote` can use: `so101_*.urdf` files and the STL meshes within `assets/`. It excludes all unused `.xml` files associated with the MuJoCo description of the robot, which Pinocchio cannot load.

## Upstream notes

A collection of pertinent details quoted from the upstream [Simulation/SO101/README.md](https://github.com/TheRobotStudio/SO-ARM100/blob/main/Simulation/SO101/README.md). References to `*.xml` and MuJoCo files describe the upstream directory, not this one. Calibration distinctions apply to the URDFs as well.

>### Calibration Methods
>
>The MuJoCo file `scene.xml` supports two differenly [sic] calibrated SO101 robot files:
>
>- **New Calibration (Default)**: Each joint's virtual zero is set to the **middle** of its joint range. Use -> `so101_new_calib.xml`. 
>- **Old Calibration**: Each joint's virtual zero is set to the configuration where the robot is **fully extended horizontally**. Use -> `so101_old_calib.xml`.
>
>To switch between calibration methods, modify the included robot file in `scene.xml`.
>
>### Motor Parameters
>
>Motor properties for the STS3215 motors used in the robot are adapted from the [Open Duck Mini project](https://github.com/apirrone/Open_Duck_Mini).
>
>### Gripper Note
>
>In LeRobot, the gripper is represented as a **linear joint**, where:
>
>* `0` = fully closed
>* `100` = fully open
>
>This mapping is **not yet reflected** in the current URDF and MuJoCo files. 

## Usage within roboremote

- **Canonical model:** `so101_new_calib.urdf`, selected via the environment variable `ROBOREMOTE_MODEL_PATH`. Set as the default in `.env.example` and baked in `physics/Dockerfile`.
- **Meshes:** `viz` resolves the STLs through the URDF's relative `assets/…` paths. `physics` builds the kinematic model only and never loads the meshes.
- **`so101_old_calib.urdf`:** retained, unused, loadable by pointing the env var at it. However, roboremote's unit tests and live operation are unvalidated with this `old_calib` model.
- **`so101_new_calib_camera.urdf`:** retained, unused, not yet validated against the controllers or gains.
- **Gripper:** ordinary revolute joint in radians; LeRobot's `0–100` linear mapping quoted above is not implemented here.
