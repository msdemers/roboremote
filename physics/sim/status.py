from enum import Enum

class SimStatus(Enum):
    UNSPECIFIED = 0
    IDLE = 1
    RUNNING = 2
    FAULT = 3

class ControlMode(Enum):
    UNSPECIFIED = 0
    GRAVITY_COMP = 1
    TASK_PD_COMPENSATED = 2
    TASK_PD_RAW = 3
    JOINT_PD_COMPENSATED = 4
    JOINT_PD_RAW = 5

class ControlDomain(Enum):
    NONE = 0
    TASK = 1
    JOINT = 2

def domain_for(mode: ControlMode) -> ControlDomain:
    match mode:
        case ControlMode.GRAVITY_COMP | ControlMode.UNSPECIFIED:
            return ControlDomain.NONE
        case ControlMode.TASK_PD_COMPENSATED | ControlMode.TASK_PD_RAW:
            return ControlDomain.TASK
        case ControlMode.JOINT_PD_COMPENSATED | ControlMode.JOINT_PD_RAW:
            return ControlDomain.JOINT
        case _:
            raise ValueError(f"unsupported control mode: {mode}")
