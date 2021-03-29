import time
from typing import Tuple, Optional

import docker

from online.statistics.providers import UsageStatsProvider


class DockerImagesProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(DockerImagesProvider, self).__init__("docker/images", frequency)
        self._client = docker.from_env()

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        try:
            images = {
                image["Id"]: image for image in self._client.api.images()
            }
            return time.time(), images
        except docker.errors.APIError:
            return None, None
