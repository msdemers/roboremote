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

