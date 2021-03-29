import time
from typing import Tuple, Optional

import requests

from dt_device_utils import get_device_hostname
from online.statistics.providers import UsageStatsProvider


class BatteryHistoryProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(BatteryHistoryProvider, self).__init__("battery/history", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        hostname = get_device_hostname()
        url = f"http://{hostname}.local/health/battery/history"
        # noinspection PyBroadException
        try:
            data = requests.get(url).json()
            return time.time(), data
        except Exception:
            return None, None
