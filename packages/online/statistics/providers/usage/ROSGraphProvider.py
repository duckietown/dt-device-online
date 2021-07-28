import time
from typing import Tuple, Optional

import requests

from dt_device_utils import get_device_hostname
from online.statistics.providers import UsageStatsProvider


class ROSGraphProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(ROSGraphProvider, self).__init__("ros/graph", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        hostname = get_device_hostname()
        url = f"http://{hostname}.local/ros/graph"
        # noinspection PyBroadException
        try:
            data = requests.get(url).json()['data']
            return time.time(), data
        except Exception:
            return None, None
