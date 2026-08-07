import numpy as np
import pinocchio as pin

def clip_joint_rom(model: pin.Model,
    q: np.ndarray,
    v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Clip joint coordinates to the range allowed by the model's joint limits. 
    Velocities moving into the joint limit are set to 0.
    """
    q_clipped = np.copy(q)
    v_clipped = np.copy(v)

    for j in range(1, model.njoints):
        joint: pin.JointModel = model.joints[j]
        if joint.nq != joint.nv:
            continue # joint limits meaningless when nq != nv. skip

        for i in range(joint.nq):
            iQ = joint.idx_q+i
            iV = joint.idx_v+i
            if q[iQ] > model.upperPositionLimit[iQ]:
                q_clipped[iQ] = model.upperPositionLimit[iQ]
                if v[iV] > 0.0:
                    v_clipped[iV] = 0.0
            if q[iQ] < model.lowerPositionLimit[iQ]:
                q_clipped[iQ] = model.lowerPositionLimit[iQ]
                if v[iV] < 0.0:
                    v_clipped[iV] = 0.0
    return q_clipped, v_clipped

