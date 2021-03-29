import time
from typing import Tuple, Optional

from dt_device_utils import get_device_hostname
from online.statistics.providers import ConfigurationStatsProvider


class RobotHostnameProvider(ConfigurationStatsProvider):

    def __init__(self):
        super(RobotHostnameProvider, self).__init__("robot/hostname")

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        data = {
            "value": get_device_hostname()
        }
        return time.time(), data
