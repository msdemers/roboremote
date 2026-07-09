from roboremote.arm.v1 import arm_pb2 as pb
import pinocchio as pin
import numpy as np
from sim.simulator import SimSnapshot, Simulator, status

_STATUS_MAP = {
    status.SimStatus.UNSPECIFIED: pb.ARM_STATUS_UNSPECIFIED,
    status.SimStatus.IDLE: pb.ARM_STATUS_IDLE,
    status.SimStatus.RUNNING: pb.ARM_STATUS_RUNNING,
    status.SimStatus.FAULT: pb.ARM_STATUS_FAULT
}

_MODE_MAP = {
    status.ControlMode.UNSPECIFIED: pb.CONTROL_MODE_UNSPECIFIED,
    status.ControlMode.GRAVITY_COMP: pb.CONTROL_MODE_GRAVITY_COMP,
    status.ControlMode.TASK_PD_COMPENSATED: pb.CONTROL_MODE_TASK_PD_COMPENSATED,
    status.ControlMode.TASK_PD_RAW: pb.CONTROL_MODE_TASK_PD_RAW,
    status.ControlMode.JOINT_PD_COMPENSATED: pb.CONTROL_MODE_JOINT_PD_COMPENSATED,
    status.ControlMode.JOINT_PD_RAW: pb.CONTROL_MODE_JOINT_PD_RAW,
}

_MODE_MAP_INV = {v: k for k, v in _MODE_MAP.items()}

def get_joint_type(joint: pin.JointModel) -> pb.JointInfo.JointType:
    """
    Maps a Pinocchio JointModel to its corresponding Protobuf JointType 
    using explicit Python class inheritance checks.
    """

    name = joint.shortname()

    # Check for Free-Flyer types
    if name.startswith("JointModelFreeFlyer"):
        return pb.JointInfo.JOINT_TYPE_FREE_FLYER

    # Check for Planar types
    elif name.startswith("JointModelPlanar"):
        return pb.JointInfo.JOINT_TYPE_PLANAR
        
    # Check for Revolute types
    elif name.startswith("JointModelR"):
        return pb.JointInfo.JOINT_TYPE_REVOLUTE
        
    # Check for Prismatic types 
    elif name.startswith("JointModelP"):
        return pb.JointInfo.JOINT_TYPE_PRISMATIC
        
    # Check for Spherical types 
    elif name.startswith("JointModelSpherical"):
        return pb.JointInfo.JOINT_TYPE_SPHERICAL
        
    # Fallback for unsupported or unmapped joints
    return pb.JointInfo.JOINT_TYPE_UNSPECIFIED

def build_model_descriptor(model: pin.Model, model_name: str, model_version: str) -> pb.ModelDescriptor:
    joints = []
    for j in range(1, model.njoints):
        joint: pin.JointModel = model.joints[j]

        ji = pb.JointInfo(
            name=model.names[j],
            id=j,
            parent_id=model.parents[j],
            type=get_joint_type(joint),
            nq=joint.nq, nv=joint.nv, idx_q=joint.idx_q, idx_v=joint.idx_v,
            position_limit_lower=model.lowerPositionLimit[joint.idx_q : joint.idx_q + joint.nq],
            position_limit_upper=model.upperPositionLimit[joint.idx_q : joint.idx_q + joint.nq],
            velocity_limit=model.velocityLimit[joint.idx_v : joint.idx_v + joint.nv],
            effort_limit=model.effortLimit[joint.idx_v : joint.idx_v + joint.nv]
        )

        joints.append(ji)

    desc = pb.ModelDescriptor(
        model_name=model_name,
        model_version=model_version,
        nq=model.nq,
        nv=model.nv,
        joints=joints
    )

    return desc

def se3_to_cartesian_pose(se3: pin.SE3) -> pb.CartesianPose:
    translation = se3.translation
    quaternion = pin.Quaternion(se3.rotation)
    return pb.CartesianPose(x=translation[0], y=translation[1], z=translation[2],
                            qx=quaternion.x, qy=quaternion.y, qz=quaternion.z, qw=quaternion.w)

def cartesian_pose_to_se3(cartesian_pose: pb.CartesianPose) -> pin.SE3:
    translation = np.array([cartesian_pose.x, cartesian_pose.y, cartesian_pose.z])
    quat = pin.Quaternion(np.array([
        cartesian_pose.qx,
        cartesian_pose.qy,
        cartesian_pose.qz,
        cartesian_pose.qw
    ]))
    quat.normalize()
    return pin.SE3(quat.matrix(), translation)

def snapshot_to_arm_state(snap: SimSnapshot) -> pb.ArmState:
    arm_state = pb.ArmState(
        status=_STATUS_MAP[snap.sim_status],
        active_mode=_MODE_MAP[snap.active_mode],
        sim_time=snap.t,
        q=pb.Coordinates(q=snap.q),
        v=pb.Velocities(v=snap.v),
        tau=pb.Actuation(tau=snap.tau),
        end_effector=se3_to_cartesian_pose(snap.ee_pose)
    )
    # handle custom logic for the oneof structure of active_target
    target = snap.active_target
    if isinstance(target, np.ndarray):
        arm_state.joint_target.CopyFrom(pb.Coordinates(q=target))
    elif isinstance(target, pin.SE3):
        arm_state.cartesian_target.CopyFrom(se3_to_cartesian_pose(target))
    
    return arm_state