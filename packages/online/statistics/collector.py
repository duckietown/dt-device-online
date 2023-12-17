import copy
import json
import os
import time
import requests
import dataclasses
from enum import Enum
from threading import Thread, Semaphore
from typing import List

import dt_authentication
from dt_authentication import DuckietownToken

from dt_class_utils import DTProcess, DTReminder
from dt_device_utils import get_device_id
from dt_permissions_utils import permission_granted
from dt_secrets_utils import get_secret
from .providers.configuration.RobotConfigurationProvider import RobotConfigurationProvider
from .providers.configuration.RobotHostnameProvider import RobotHostnameProvider
from .providers.configuration.RobotTypeProvider import RobotTypeProvider
from .providers.usage.BatteryHistoryProvider import BatteryHistoryProvider
from .providers.usage.BatteryInfoProvider import BatteryInfoProvider
from .providers.usage.DockerImagesProvider import DockerImagesProvider
from .providers.usage.GeolocationProvider import GeolocationProvider
from .providers.usage.HealthProvider import HealthProvider
from .providers.usage.LSUSBProvider import LSUSBProvider
from .providers.usage.PublicIPProvider import PublicIPProvider
from .providers.usage.ROSGraphProvider import ROSGraphProvider
from .providers.usage.UptimeProvider import UptimeProvider
from .providers.usage.NetworkConfigurationProvider import NetworkConfigurationProvider
from .providers.usage.WirelessStatusProvider import WirelessStatusProvider

from ..constants import \
    STATS_CATEGORY_TO_DIR, \
    STATS_PUBLISHER_PERIOD_SECS, \
    FREQUENCY, \
    STATS_API_URL, \
    STATS_BOOT_ID_FILE

from .providers import StatisticsProvider
from .providers.event import glob_event_providers
from .providers.usage import glob_usage_providers
from .providers.usage.DockerPSProvider import DockerPSProvider


class StatisticsCategory(Enum):
    EVENT = "event"
    USAGE = "usage"
    CONFIGURATION = "configuration"


@dataclasses.dataclass
class StatisticsPoint:
    category: StatisticsCategory
    key: str
    device: str
    stamp: float
    payload: dict
    provider: StatisticsProvider
    format: str = "1"

    def __str__(self):
        return json.dumps({
            "category": self.category.value,
            "key": self.key,
            "device": self.device,
            "stamp": self.stamp,
            "format": self.format,
            "payload": self.payload
        })


class StatisticsWorker(Thread):

    def __init__(self):
        super().__init__()
        events_dir = STATS_CATEGORY_TO_DIR["event"]
        usage_dir = STATS_CATEGORY_TO_DIR["usage"]
        # ---
        self._shutdown = False
        self._providers: List[StatisticsProvider] = []
        self._outbox = StatisticsUploader()
        self._timer = DTReminder(frequency=FREQUENCY.EVERY_MINUTE)
        # register providers
        # - stats/events/ dir
        print("Initializing provider 'stats/events'...")
        self._providers.extend(glob_event_providers(events_dir, "*.json"))
        print("Provider 'stats/events' initialized!")
        # - stats/usage/disk_image/ dir
        print("Initializing provider 'stats/usage/disk_image'...")
        self._providers.extend(glob_usage_providers(
            os.path.join(usage_dir, "disk_image"), "*.json", "disk_image"))
        print("Provider 'stats/usage/disk_image' initialized!")
        # - stats/usage/init_sd_card/ dir
        print("Initializing provider 'stats/usage/init_sd_card'...")
        self._providers.extend(glob_usage_providers(
            os.path.join(usage_dir, "init_sd_card"), "*.json", "init_sd_card"))
        print("Provider 'stats/usage/init_sd_card' initialized!")
        # - docker/ps
        print("Initializing provider 'DockerPSProvider'...")
        self._providers.append(DockerPSProvider(FREQUENCY.EVERY_MINUTE))
        print("Provider 'DockerPSProvider' initialized!")
        # - docker/images
        print("Initializing provider 'DockerImagesProvider'...")
        self._providers.append(DockerImagesProvider(FREQUENCY.EVERY_MINUTE))
        print("Provider 'DockerImagesProvider' initialized!")
        # - uptime
        print("Initializing provider 'UptimeProvider'...")
        self._providers.append(UptimeProvider(FREQUENCY.EVERY_30_MINUTES))
        print("Provider 'UptimeProvider' initialized!")
        # - network/configuration
        print("Initializing provider 'NetworkConfigurationProvider'...")
        self._providers.append(NetworkConfigurationProvider(FREQUENCY.EVERY_1_HOUR))
        print("Provider 'NetworkConfigurationProvider' initialized!")
        # - ros/graph
        print("Initializing provider 'ROSGraphProvider'...")
        self._providers.append(ROSGraphProvider(FREQUENCY.EVERY_30_MINUTES))
        print("Provider 'ROSGraphProvider' initialized!")
        # - health
        print("Initializing provider 'HealthProvider'...")
        self._providers.append(HealthProvider(FREQUENCY.EVERY_30_MINUTES))
        print("Provider 'HealthProvider' initialized!")
        # - network/public_ip
        print("Initializing provider 'PublicIPProvider'...")
        self._providers.append(PublicIPProvider(FREQUENCY.ONESHOT))
        print("Provider 'PublicIPProvider' initialized!")
        # - geolocation
        print("Initializing provider 'GeolocationProvider'...")
        self._providers.append(GeolocationProvider(FREQUENCY.ONESHOT))
        print("Provider 'GeolocationProvider' initialized!")
        # - battery/history
        print("Initializing provider 'BatteryHistoryProvider'...")
        self._providers.append(BatteryHistoryProvider(FREQUENCY.EVERY_2_HOURS))
        print("Provider 'BatteryHistoryProvider' initialized!")
        # - battery/info
        print("Initializing provider 'BatteryInfoProvider'...")
        self._providers.append(BatteryInfoProvider(FREQUENCY.ONESHOT))
        print("Provider 'BatteryInfoProvider' initialized!")
        # - lsusb
        print("Initializing provider 'LSUSBProvider'...")
        self._providers.append(LSUSBProvider(FREQUENCY.EVERY_2_HOURS))
        print("Provider 'LSUSBProvider' initialized!")
        # - wireless/status
        print("Initializing provider 'WirelessStatusProvider'...")
        self._providers.append(WirelessStatusProvider(FREQUENCY.EVERY_30_MINUTES))
        print("Provider 'WirelessStatusProvider' initialized!")
        # - robot/hostname
        print("Initializing provider 'RobotHostnameProvider'...")
        self._providers.append(RobotHostnameProvider())
        print("Provider 'RobotHostnameProvider' initialized!")
        # - robot/type
        print("Initializing provider 'RobotTypeProvider'...")
        self._providers.append(RobotTypeProvider())
        print("Provider 'RobotTypeProvider' initialized!")
        # - robot/configuration
        print("Initializing provider 'RobotConfigurationProvider'...")
        self._providers.append(RobotConfigurationProvider())
        print("Provider 'RobotConfigurationProvider' initialized!")
        # launch outbox
        self._outbox.start()

    def is_shutdown(self) -> bool:
        return self._shutdown

    def shutdown(self):
        self._outbox.shutdown()
        self._shutdown = True

    def run(self):
        app = DTProcess.get_instance()
        # (try to) read the device ID
        try:
            device_id = get_device_id()
        except ValueError:
            # no device ID? nothing to do
            app.logger.warning("Could not find the device's unique ID. Cannot share stats.")
            return
        # this process gets data from a bunch of stats providers and places them in the outbox
        while not app.is_shutdown():
            # don't do this constantly
            if not self._timer.is_time():
                time.sleep(1)
                continue
            # temporary structures
            to_remove = []
            # go through the providers
            for provider in self._providers:
                if provider.istime:
                    # get timestamp and payload
                    stamp, payload = provider.data
                    if stamp is None or payload is None:
                        continue
                    # format payload
                    payload = provider.format(payload)
                    # pack data into a point
                    point = StatisticsPoint(
                        category=StatisticsCategory(provider.category),
                        key=provider.key,
                        device=device_id,
                        stamp=stamp,
                        payload=payload,
                        provider=provider
                    )
                    # add point to outbox
                    self._outbox.add(point)
                    # remove exhausted providers
                    if provider.one_shot:
                        to_remove.append(provider)
            # remove providers
            self._providers = list(filter(lambda p: p not in to_remove, self._providers))


class StatisticsUploader(Thread):

    def __init__(self):
        super(StatisticsUploader, self).__init__()
        self._shutdown = False
        self._queue: List[StatisticsPoint] = []
        # read boot ID
        with open(STATS_BOOT_ID_FILE, 'rt') as fin:
            self._boot_id = fin.read().strip()
        # create resource lock for the queue
        self._lock = Semaphore(1)

    def add(self, point: StatisticsPoint):
        with self._lock:
            self._queue.append(point)

    def is_shutdown(self) -> bool:
        return self._shutdown

    def shutdown(self):
        self._shutdown = True

    def run(self):
        app = DTProcess.get_instance()
        # read the permissions
        granted = permission_granted('allow_push_stats_data')
        if not granted:
            app.logger.warning("Permission 'allow_push_stats_data' not granted. Won't share data.")
            return
        # (try to) read the token
        try:
            token = get_secret('tokens/dt1')
            DuckietownToken.from_string(token)
        except FileNotFoundError:
            # no token? nothing to do
            app.logger.warning('No secret token dt1 found. Cannot share statistics.')
            return
        except dt_authentication.InvalidToken as e:
            # no token? nothing to do
            app.logger.warning(f'{str(e)}. Cannot share statistics.')
            return
        # if we are it means that the user agreed to share their data
        counter = 0
        while not self.is_shutdown():
            if counter % STATS_PUBLISHER_PERIOD_SECS == 0:
                counter = 1
                done = []
                with self._lock:
                    queue: List[StatisticsPoint] = copy.copy(self._queue)
                # publish
                for point in queue:
                    # publish
                    url = STATS_API_URL.format(category=point.category.value)
                    # data to send to the server
                    data: dict = {
                        "key": point.key,
                        "device": point.device,
                        "boot_id": self._boot_id,
                        # the server is expecting milliseconds, we worked with seconds float so far
                        "stamp": int(point.stamp * 1000),
                        "format": point.format,
                        "payload": point.payload,
                    }
                    # authentication data
                    headers: dict = {"Authorization": f"Token {token}"}
                    # make request
                    res = requests.post(url, json=data, headers=headers)
                    try:
                        assert res.status_code == 200
                        res = res.json()
                        assert 'success' in res
                        if res['success']:
                            # cleanup provider resource
                            point.provider.cleanup()
                            # mark it as DONE
                            done.append(point)
                        else:
                            if res.get("code", 0) == 409:
                                # this data point already exists
                                # cleanup provider resource
                                point.provider.cleanup()
                                # mark it as DONE
                                done.append(point)
                            else:
                                app.logger.debug(str(res))

                    except (Exception, AssertionError) as e:
                        app.logger.debug(str(e))
                # remove correctly uploaded points from queue
                with self._lock:
                    self._queue = list(filter(lambda p: p not in done, self._queue))
            # ---
            time.sleep(1)
            counter += 1
