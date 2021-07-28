import time
from typing import Tuple, Optional

import docker

from online.statistics.providers import UsageStatsProvider


class DockerPSProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(DockerPSProvider, self).__init__("docker/ps", frequency)
        self._client = docker.from_env()
        self._last = None

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        data = {}
        try:
            # get list of containers
            containers = self._client.containers.list(sparse=True)
            # compute the current set of container IDs
            current = set(map(lambda c: c.id, containers))
            if current == self._last:
                # no changes since last time we checked, do not report
                return None, None
            # inspect containers
            for container in containers:
                data[container.id] = self._client.api.inspect_container(container.id)
            # store current set
            self._last = current
            # ---
            return time.time(), data
        except docker.errors.APIError:
            return None, None
