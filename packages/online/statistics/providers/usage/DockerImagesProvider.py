import time
from typing import Tuple, Optional

import docker

from online.statistics.providers import UsageStatsProvider


class DockerImagesProvider(UsageStatsProvider):

    def __init__(self, frequency: float):
        super(DockerImagesProvider, self).__init__("docker/images", frequency)
        self._client = docker.from_env()
        self._last = None

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        try:
            # get list of images
            images = {
                image["Id"]: image for image in self._client.api.images()
            }
            # compute the current set of image IDs
            current = set(images.keys())
            if current == self._last:
                # no changes since last time we checked, do not report
                return None, None
            # store current set
            self._last = current
            # ---
            return time.time(), images
        except docker.errors.APIError:
            return None, None
