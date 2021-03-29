import time
from typing import Tuple, Optional

import docker

from online.statistics.providers import UsageStatsProvider


class DockerPSProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(DockerPSProvider, self).__init__("docker/ps", frequency)
        self._client = docker.from_env()

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        data = {}
        try:
            for container in self._client.containers.list(sparse=True):
                data[container.id] = self._client.api.inspect_container(container.id)
            return time.time(), data
        except docker.errors.APIError:
            return None, None
