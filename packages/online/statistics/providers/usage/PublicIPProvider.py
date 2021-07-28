import time
from typing import Tuple, Optional

import requests

from online.statistics.providers import UsageStatsProvider


class PublicIPProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(PublicIPProvider, self).__init__("network/public_ip", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        url = "https://api.ipify.org?format=json"
        # noinspection PyBroadException
        try:
            data = requests.get(url).json()
            return time.time(), data
        except Exception:
            return None, None
