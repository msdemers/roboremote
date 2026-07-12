from sim.status import ControlMode
from . import controllers
import pinocchio as pin
import numpy as np

def controller_for(mode: ControlMode, target: np.ndarray | pin.SE3 | None =None) -> controllers.Controller:
    match mode:
        case ControlMode.GRAVITY_COMP:
            return controllers.GravityCompensationController()
        case ControlMode.JOINT_PD_COMPENSATED:
            return controllers.JointPdController(target)
        case ControlMode.TASK_PD_COMPENSATED:
            return controllers.TaskPdController(target)
        case ControlMode.JOINT_PD_RAW:
            return controllers.JointRawPdController(target)
        case ControlMode.TASK_PD_RAW:
            return controllers.TaskRawPdController(target)
        case _:
            raise ValueError(f"unsupported control mode: {mode}")
