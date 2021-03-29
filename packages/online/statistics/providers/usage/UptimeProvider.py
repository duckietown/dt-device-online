import time
from typing import Tuple, Optional

import psutil

from online.statistics.providers import UsageStatsProvider


class UptimeProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(UptimeProvider, self).__init__("uptime", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        data = {"uptime": time.time() - psutil.boot_time()}
        return time.time(), data
