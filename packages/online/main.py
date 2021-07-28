import time

from dt_class_utils import DTProcess
from online.statistics.collector import StatisticsWorker

from .autobackup import AutoBackupWorker


class DeviceOnlineApp(DTProcess):

    def __init__(self):
        super().__init__()
        self._backup_worker = AutoBackupWorker()
        self._statistics_worker = StatisticsWorker()
        # start backup worker
        self._backup_worker.start()
        # start statistics collector worker
        self._statistics_worker.start()
        # register shutdown
        self.register_shutdown_callback(self._backup_worker.shutdown)
        self.register_shutdown_callback(self._statistics_worker.shutdown)
        # keep process alive
        while not self.is_shutdown():
            time.sleep(1)


if __name__ == '__main__':
    app = DeviceOnlineApp()
