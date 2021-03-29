import time
import iwlib
from typing import Tuple, Optional

from online.statistics.providers import UsageStatsProvider

WIFI_DEVICE = "wlan0"


class WirelessStatusProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(WirelessStatusProvider, self).__init__("wireless/status", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        try:
            data = iwlib.get_iwconfig(WIFI_DEVICE)
            data = {k: v.decode('utf-8') if isinstance(v, bytes) else v for k, v in data.items()}
            return time.time(), data
        except (Exception, OSError):
            return None, None
