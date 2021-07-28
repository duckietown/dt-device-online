import abc
import json
import os
from typing import Optional, Tuple

from dt_class_utils import DTReminder


class StatisticsProvider(abc.ABC):

    def __init__(self, category: str, key: str, frequency: float):
        self._category = category
        self._key = key
        self._frequency = frequency or 0
        self._ever_run = False
        self._reminder = None if self.one_shot else DTReminder(frequency=self._frequency)

    @property
    def category(self) -> str:
        return self._category

    @property
    def key(self) -> str:
        return self._key

    @property
    def data(self) -> Tuple[Optional[float], Optional[dict]]:
        return self.step()

    @property
    def one_shot(self) -> bool:
        return self._frequency <= 0

    @property
    def istime(self) -> bool:
        if not self._ever_run:
            self._ever_run = True
            return True
        return self._reminder.is_time() if self._reminder else True

    @abc.abstractmethod
    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        pass

    def cleanup(self):
        pass

    @staticmethod
    def format(data: dict) -> dict:
        # this is a passthrough by default
        return data


class UsageStatsProvider(StatisticsProvider):

    def __init__(self, key: str, frequency: float):
        super(UsageStatsProvider, self).__init__("usage", key, frequency)

    @abc.abstractmethod
    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        pass


class EventStatsProvider(StatisticsProvider):

    def __init__(self, key: str, frequency: float):
        super(EventStatsProvider, self).__init__("event", key, frequency)

    @abc.abstractmethod
    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        pass


class ConfigurationStatsProvider(StatisticsProvider):

    def __init__(self, key: str):
        super(ConfigurationStatsProvider, self).__init__("configuration", key, 0)

    @abc.abstractmethod
    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        pass


class FileStatsProvider(StatisticsProvider):

    def __init__(self, category: str, key: Optional[str], filepath: str):
        super(FileStatsProvider, self).__init__(category, key, 0)
        self._filepath = os.path.abspath(filepath)
        self._content = None
        # noinspection PyBroadException
        try:
            with open(self._filepath, 'rt') as fin:
                self._content = json.load(fin)
        except Exception:
            pass

    @property
    def istime(self) -> bool:
        # no need to check `super()`, we know it is always True given that `frequency` is 0
        return self._content is not None and self._key is not None

    @abc.abstractmethod
    def step(self) -> Tuple[Optional[float], Optional[dict]]:
        pass
