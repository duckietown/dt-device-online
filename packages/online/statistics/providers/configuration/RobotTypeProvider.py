import time
from typing import Tuple, Optional

from dt_robot_utils import get_robot_type, get_robot_configuration, RobotType, RobotConfiguration
from online.statistics.providers import ConfigurationStatsProvider


class RobotTypeProvider(ConfigurationStatsProvider):

    def __init__(self):
        super(RobotTypeProvider, self).__init__("robot/type")

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        rtype = get_robot_type()
        if rtype == RobotType.UNKNOWN:
            return None, None
        # ---
        data = {
            "value": rtype.name.lower()
        }
        return time.time(), data
