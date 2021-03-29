import time
from typing import Tuple, Optional

import requests

from dt_device_utils import get_device_hostname
from online.statistics.providers import UsageStatsProvider


class BatteryInfoProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(BatteryInfoProvider, self).__init__("battery/info", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        hostname = get_device_hostname()
        url = f"http://{hostname}.local/health/battery/info"
        # noinspection PyBroadException
        try:
            data = requests.get(url).json()
            return time.time(), data
        except Exception:
            return None, None
