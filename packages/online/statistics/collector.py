import copy
import json
import os
import time
from enum import Enum
from threading import Thread, Semaphore
from typing import List

import dataclasses
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
    STATS_PUBLISHER_PERIOD, \
    FREQUENCY

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
    # TODO: the API will add
    # - uid
    # - stamp_received
    # - api (version)
    # - IP

    def __str__(self):
        return json.dumps({
            "category": self.category.value,
            "key": self.key,
            "device": self.device,
            "stamp": self.stamp,
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
        self._timer = DTReminder(frequency=FREQUENCY.EVERY_10_SECONDS)
        # register providers
        # - stats/events/ dir
        self._providers.extend(glob_event_providers(events_dir, "*.json"))
        # - stats/usage/ dirs
        self._providers.extend(glob_usage_providers(
            os.path.join(usage_dir, "disk_image"), "*.json", "disk_image"))
        self._providers.extend(glob_usage_providers(
            os.path.join(usage_dir, "init_sd_card"), "*.json", "init_sd_card"))
        # - docker/ps
        self._providers.append(DockerPSProvider(FREQUENCY.EVERY_1_HOUR))
        # - docker/images
        self._providers.append(DockerImagesProvider(FREQUENCY.EVERY_2_HOURS))
        # - uptime
        self._providers.append(UptimeProvider(FREQUENCY.EVERY_30_MINUTES))
        # - network/configuration
        self._providers.append(NetworkConfigurationProvider(FREQUENCY.EVERY_1_HOUR))
        # - ros/graph
        self._providers.append(ROSGraphProvider(FREQUENCY.EVERY_30_MINUTES))
        # - health
        self._providers.append(HealthProvider(FREQUENCY.EVERY_30_MINUTES))
        # - network/public_ip
        self._providers.append(PublicIPProvider(FREQUENCY.ONESHOT))
        # - geolocation
        self._providers.append(GeolocationProvider(FREQUENCY.ONESHOT))
        # - battery/history
        self._providers.append(BatteryHistoryProvider(FREQUENCY.EVERY_2_HOURS))
        # - battery/info
        self._providers.append(BatteryInfoProvider(FREQUENCY.ONESHOT))
        # - lsusb
        self._providers.append(LSUSBProvider(FREQUENCY.EVERY_2_HOURS))
        # - wireless/status
        self._providers.append(WirelessStatusProvider(FREQUENCY.EVERY_30_MINUTES))
        # - robot/hostname
        self._providers.append(RobotHostnameProvider())
        # - robot/type
        self._providers.append(RobotTypeProvider())
        # - robot/configuration
        self._providers.append(RobotConfigurationProvider())
        # launch outbox
        self._outbox.start()

    def is_shutdown(self) -> bool:
        return self._shutdown

    def shutdown(self):
        self._outbox.shutdown()
        self._shutdown = True

    def run(self):
        app = DTProcess.get_instance()
        # (try to) read the token
        try:
            token = get_secret('tokens/dt1')
            DuckietownToken.from_string(token)
        except FileNotFoundError:
            # no token? nothing to do
            app.logger.warning('No secret token dt1 found. Cannot collect statistics.')
            return
        except dt_authentication.InvalidToken as e:
            # no token? nothing to do
            app.logger.warning(f'{str(e)}. Cannot collect statistics.')
            return
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
            #


class StatisticsUploader(Thread):

    def __init__(self):
        super(StatisticsUploader, self).__init__()
        self._shutdown = False
        self._queue: List[StatisticsPoint] = []
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
        # if we are it means that the user agreed to share their data
        counter = 0
        while not self.is_shutdown():
            if counter % STATS_PUBLISHER_PERIOD == 0:
                done = []
                with self._lock:
                    queue = copy.copy(self._queue)
                # publish
                for point in queue:
                    print("PUBLISHING:")
                    print(point)
                    # cleanup provider resource
                    point.provider.cleanup()
                    # mark is as DONE
                    done.append(point)
                    print("-" * 30)
                    print()
                # remove correctly uploaded points from queue
                with self._lock:
                    self._queue = list(filter(lambda p: p not in done, self._queue))
            # ---
            time.sleep(1)
            counter += 1