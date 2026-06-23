import numpy as np
import pinocchio as pin

EE_FRAME = "gripper_frame_link"

def end_effector_pose(model: pin.Model, data: pin.Data, q: np.ndarray):
    """Forward kinematics: joint configuration → end-effector pose in the world frame.

    Args:
        model: pin.Model built from the SO-101 URDF (requires named frame "gripper_frame_link").
        data:  pin.Data created from `model` (caller owns it; we mutate in place).
        q:     configuration vector, shape (model.nq,), radians.

    Returns:
        A pin.SE3
    """
    if not model.existFrame(EE_FRAME):
        raise ValueError(
            f"Frame '{EE_FRAME}' does not exist in the loaded model."
        )
    frameID = model.getFrameId(EE_FRAME)
    pin.framesForwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)
    return data.oMf[frameID]