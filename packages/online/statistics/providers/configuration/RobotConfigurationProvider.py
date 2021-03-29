import time
from typing import Tuple, Optional

from dt_robot_utils import get_robot_configuration, RobotConfiguration
from online.statistics.providers import ConfigurationStatsProvider


class RobotConfigurationProvider(ConfigurationStatsProvider):

    def __init__(self):
        super(RobotConfigurationProvider, self).__init__("robot/configuration")

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        rconfiguration = get_robot_configuration()
        if rconfiguration == RobotConfiguration.UNKNOWN:
            return None, None
        # ---
        data = {
            "value": rconfiguration.name
        }
        return time.time(), data
