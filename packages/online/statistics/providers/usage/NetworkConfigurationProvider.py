import re
import time
import netifaces
from typing import Tuple, Optional

from online.statistics.providers import UsageStatsProvider


IFACES_TO_MONITOR = [
    "eth[0-9]",
    "wlan[0-9]",
    "tun[0-9]",
    "tap[0-9]"
]


class NetworkConfigurationProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(NetworkConfigurationProvider, self).__init__("network/configuration", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        data = {}
        ifaces = netifaces.interfaces()
        for iface in ifaces:
            match = False
            for miface in IFACES_TO_MONITOR:
                if re.match(miface, iface):
                    match = True
                    break
            if not match:
                continue
            # ---
            addrs = netifaces.ifaddresses(iface)
            addrs = {
                netifaces.address_families[af]: addr
                for af, addr in addrs.items()
            }
            data[iface] = addrs
        # ---
        return time.time(), data
