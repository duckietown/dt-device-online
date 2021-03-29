import os
from typing import Tuple, Optional

from online.statistics.providers import FileStatsProvider


class GenericFileUsageProvider(FileStatsProvider):

    def __init__(self, key: str, filepath: str):
        super(GenericFileUsageProvider, self).__init__("usage", key, filepath)
        if self._content is None or "stamp" not in self._content:
            return
        self._stamp = self._content["stamp"]

    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        return self._stamp, self._content

    def cleanup(self):
        print(f"Deleting '{self._filepath}'")
        # TODO: re-enable
        # os.remove(self._filepath)
