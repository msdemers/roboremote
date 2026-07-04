from roboremote.arm.v1 import arm_pb2 as pb
import pinocchio as pin
import numpy as np

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