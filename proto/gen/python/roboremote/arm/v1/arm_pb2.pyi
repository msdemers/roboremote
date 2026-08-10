from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ArmStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ARM_STATUS_UNSPECIFIED: _ClassVar[ArmStatus]
    ARM_STATUS_IDLE: _ClassVar[ArmStatus]
    ARM_STATUS_RUNNING: _ClassVar[ArmStatus]
    ARM_STATUS_FAULT: _ClassVar[ArmStatus]

class ControlMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTROL_MODE_UNSPECIFIED: _ClassVar[ControlMode]
    CONTROL_MODE_GRAVITY_COMP: _ClassVar[ControlMode]
    CONTROL_MODE_TASK_PD_COMPENSATED: _ClassVar[ControlMode]
    CONTROL_MODE_TASK_PD_RAW: _ClassVar[ControlMode]
    CONTROL_MODE_JOINT_PD_COMPENSATED: _ClassVar[ControlMode]
    CONTROL_MODE_JOINT_PD_RAW: _ClassVar[ControlMode]

class StreamRate(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STREAM_RATE_UNSPECIFIED: _ClassVar[StreamRate]
    STREAM_RATE_30: _ClassVar[StreamRate]
    STREAM_RATE_60: _ClassVar[StreamRate]
    STREAM_RATE_120: _ClassVar[StreamRate]
ARM_STATUS_UNSPECIFIED: ArmStatus
ARM_STATUS_IDLE: ArmStatus
ARM_STATUS_RUNNING: ArmStatus
ARM_STATUS_FAULT: ArmStatus
CONTROL_MODE_UNSPECIFIED: ControlMode
CONTROL_MODE_GRAVITY_COMP: ControlMode
CONTROL_MODE_TASK_PD_COMPENSATED: ControlMode
CONTROL_MODE_TASK_PD_RAW: ControlMode
CONTROL_MODE_JOINT_PD_COMPENSATED: ControlMode
CONTROL_MODE_JOINT_PD_RAW: ControlMode
STREAM_RATE_UNSPECIFIED: StreamRate
STREAM_RATE_30: StreamRate
STREAM_RATE_60: StreamRate
STREAM_RATE_120: StreamRate

class Coordinates(_message.Message):
    __slots__ = ("q",)
    Q_FIELD_NUMBER: _ClassVar[int]
    q: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, q: _Optional[_Iterable[float]] = ...) -> None: ...

class Velocities(_message.Message):
    __slots__ = ("v",)
    V_FIELD_NUMBER: _ClassVar[int]
    v: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, v: _Optional[_Iterable[float]] = ...) -> None: ...

class Actuation(_message.Message):
    __slots__ = ("tau",)
    TAU_FIELD_NUMBER: _ClassVar[int]
    tau: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, tau: _Optional[_Iterable[float]] = ...) -> None: ...

class CartesianPose(_message.Message):
    __slots__ = ("x", "y", "z", "qx", "qy", "qz", "qw")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    QX_FIELD_NUMBER: _ClassVar[int]
    QY_FIELD_NUMBER: _ClassVar[int]
    QZ_FIELD_NUMBER: _ClassVar[int]
    QW_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    qx: float
    qy: float
    qz: float
    qw: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ..., qx: _Optional[float] = ..., qy: _Optional[float] = ..., qz: _Optional[float] = ..., qw: _Optional[float] = ...) -> None: ...

class ArmState(_message.Message):
    __slots__ = ("status", "active_mode", "joint_target", "cartesian_target", "sim_time", "q", "v", "tau", "end_effector")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_MODE_FIELD_NUMBER: _ClassVar[int]
    JOINT_TARGET_FIELD_NUMBER: _ClassVar[int]
    CARTESIAN_TARGET_FIELD_NUMBER: _ClassVar[int]
    SIM_TIME_FIELD_NUMBER: _ClassVar[int]
    Q_FIELD_NUMBER: _ClassVar[int]
    V_FIELD_NUMBER: _ClassVar[int]
    TAU_FIELD_NUMBER: _ClassVar[int]
    END_EFFECTOR_FIELD_NUMBER: _ClassVar[int]
    status: ArmStatus
    active_mode: ControlMode
    joint_target: Coordinates
    cartesian_target: CartesianPose
    sim_time: float
    q: Coordinates
    v: Velocities
    tau: Actuation
    end_effector: CartesianPose
    def __init__(self, status: _Optional[_Union[ArmStatus, str]] = ..., active_mode: _Optional[_Union[ControlMode, str]] = ..., joint_target: _Optional[_Union[Coordinates, _Mapping]] = ..., cartesian_target: _Optional[_Union[CartesianPose, _Mapping]] = ..., sim_time: _Optional[float] = ..., q: _Optional[_Union[Coordinates, _Mapping]] = ..., v: _Optional[_Union[Velocities, _Mapping]] = ..., tau: _Optional[_Union[Actuation, _Mapping]] = ..., end_effector: _Optional[_Union[CartesianPose, _Mapping]] = ...) -> None: ...

class JointInfo(_message.Message):
    __slots__ = ("name", "id", "parent_id", "type", "nq", "nv", "idx_q", "idx_v", "position_limit_lower", "position_limit_upper", "velocity_limit", "effort_limit")
    class JointType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        JOINT_TYPE_UNSPECIFIED: _ClassVar[JointInfo.JointType]
        JOINT_TYPE_REVOLUTE: _ClassVar[JointInfo.JointType]
        JOINT_TYPE_PRISMATIC: _ClassVar[JointInfo.JointType]
        JOINT_TYPE_SPHERICAL: _ClassVar[JointInfo.JointType]
        JOINT_TYPE_PLANAR: _ClassVar[JointInfo.JointType]
        JOINT_TYPE_FREE_FLYER: _ClassVar[JointInfo.JointType]
        JOINT_TYPE_FIXED: _ClassVar[JointInfo.JointType]
    JOINT_TYPE_UNSPECIFIED: JointInfo.JointType
    JOINT_TYPE_REVOLUTE: JointInfo.JointType
    JOINT_TYPE_PRISMATIC: JointInfo.JointType
    JOINT_TYPE_SPHERICAL: JointInfo.JointType
    JOINT_TYPE_PLANAR: JointInfo.JointType
    JOINT_TYPE_FREE_FLYER: JointInfo.JointType
    JOINT_TYPE_FIXED: JointInfo.JointType
    NAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    PARENT_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NQ_FIELD_NUMBER: _ClassVar[int]
    NV_FIELD_NUMBER: _ClassVar[int]
    IDX_Q_FIELD_NUMBER: _ClassVar[int]
    IDX_V_FIELD_NUMBER: _ClassVar[int]
    POSITION_LIMIT_LOWER_FIELD_NUMBER: _ClassVar[int]
    POSITION_LIMIT_UPPER_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_LIMIT_FIELD_NUMBER: _ClassVar[int]
    EFFORT_LIMIT_FIELD_NUMBER: _ClassVar[int]
    name: str
    id: int
    parent_id: int
    type: JointInfo.JointType
    nq: int
    nv: int
    idx_q: int
    idx_v: int
    position_limit_lower: _containers.RepeatedScalarFieldContainer[float]
    position_limit_upper: _containers.RepeatedScalarFieldContainer[float]
    velocity_limit: _containers.RepeatedScalarFieldContainer[float]
    effort_limit: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, name: _Optional[str] = ..., id: _Optional[int] = ..., parent_id: _Optional[int] = ..., type: _Optional[_Union[JointInfo.JointType, str]] = ..., nq: _Optional[int] = ..., nv: _Optional[int] = ..., idx_q: _Optional[int] = ..., idx_v: _Optional[int] = ..., position_limit_lower: _Optional[_Iterable[float]] = ..., position_limit_upper: _Optional[_Iterable[float]] = ..., velocity_limit: _Optional[_Iterable[float]] = ..., effort_limit: _Optional[_Iterable[float]] = ...) -> None: ...

class ModelDescriptor(_message.Message):
    __slots__ = ("model_name", "model_version", "nq", "nv", "joints")
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    NQ_FIELD_NUMBER: _ClassVar[int]
    NV_FIELD_NUMBER: _ClassVar[int]
    JOINTS_FIELD_NUMBER: _ClassVar[int]
    model_name: str
    model_version: str
    nq: int
    nv: int
    joints: _containers.RepeatedCompositeFieldContainer[JointInfo]
    def __init__(self, model_name: _Optional[str] = ..., model_version: _Optional[str] = ..., nq: _Optional[int] = ..., nv: _Optional[int] = ..., joints: _Optional[_Iterable[_Union[JointInfo, _Mapping]]] = ...) -> None: ...

class StreamEnvelope(_message.Message):
    __slots__ = ("descriptor", "state")
    DESCRIPTOR_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    descriptor: ModelDescriptor
    state: ArmState
    def __init__(self, descriptor: _Optional[_Union[ModelDescriptor, _Mapping]] = ..., state: _Optional[_Union[ArmState, _Mapping]] = ...) -> None: ...

class SubscribeRequest(_message.Message):
    __slots__ = ("rate",)
    RATE_FIELD_NUMBER: _ClassVar[int]
    rate: StreamRate
    def __init__(self, rate: _Optional[_Union[StreamRate, str]] = ...) -> None: ...

class SetControlModeRequest(_message.Message):
    __slots__ = ("mode",)
    MODE_FIELD_NUMBER: _ClassVar[int]
    mode: ControlMode
    def __init__(self, mode: _Optional[_Union[ControlMode, str]] = ...) -> None: ...

class SetControlModeResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SetTargetRequest(_message.Message):
    __slots__ = ("joint_coordinates", "cartesian_pose")
    JOINT_COORDINATES_FIELD_NUMBER: _ClassVar[int]
    CARTESIAN_POSE_FIELD_NUMBER: _ClassVar[int]
    joint_coordinates: Coordinates
    cartesian_pose: CartesianPose
    def __init__(self, joint_coordinates: _Optional[_Union[Coordinates, _Mapping]] = ..., cartesian_pose: _Optional[_Union[CartesianPose, _Mapping]] = ...) -> None: ...

class SetTargetResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResetConfigurationRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ResetConfigurationResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
