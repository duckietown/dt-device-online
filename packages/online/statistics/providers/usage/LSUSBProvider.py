import re
import subprocess
import time
from typing import Tuple, Optional

from online.statistics.providers import UsageStatsProvider


class LSUSBProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(LSUSBProvider, self).__init__("lsusb", frequency)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        device_re = re.compile(
            "Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$",
            re.I)
        df = subprocess.check_output("lsusb").decode('utf-8')
        devices = []
        for i in df.split('\n'):
            if i:
                info = device_re.match(i)
                if info:
                    dinfo = info.groupdict()
                    dinfo['device'] = '/dev/bus/usb/%s/%s' % (
                        dinfo.pop('bus'), dinfo.pop('device'))
                    devices.append(dinfo)
        return time.time(), {'devices': devices}
