import time
from typing import Tuple, Optional

import requests

from online.statistics.providers import UsageStatsProvider


class GeolocationProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(GeolocationProvider, self).__init__("geolocation", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        url = "https://freegeoip.app/json/"
        # noinspection PyBroadException
        try:
            data = requests.get(url).json()
            return time.time(), data
        except Exception:
            return None, None
