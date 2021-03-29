import time
from typing import Tuple, Optional

from online.statistics.providers import UsageStatsProvider


class _TemplateUsageProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(_TemplateUsageProvider, self).__init__("XXXXXXXXXX", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        return time.time(), {}
