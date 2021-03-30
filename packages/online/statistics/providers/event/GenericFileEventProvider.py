import os
from typing import Tuple, Optional

from online.statistics.providers import FileStatsProvider


class GenericFileEventProvider(FileStatsProvider):

    def __init__(self, filepath: str):
        super(GenericFileEventProvider, self).__init__("event", "null", filepath)
        if self._content is None or "type" not in self._content or "stamp" not in self._content:
            return
        self._key = self._content["type"]
        # events represent their timestamps in nanoseconds, use seconds instead
        self._stamp = self._content["stamp"] / (10 ** 9)

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        data = self._content.get("data", "{}")
        return self._stamp, data

    def cleanup(self):
        os.remove(self._filepath)
