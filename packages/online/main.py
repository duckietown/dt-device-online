from dt_class_utils import DTProcess

from .broadcaster import GlobalBroadcaster
from .autobackup import AutoBackupWorker


class DeviceOnlineApp(DTProcess):

    def __init__(self):
        super().__init__()
        self._broadcaster = GlobalBroadcaster()
        self._backup_worker = AutoBackupWorker()
        # start broadcaster
        self._backup_worker.start()
        self._broadcaster.start()
        # join workers
        self._backup_worker.join()


if __name__ == '__main__':
    app = DeviceOnlineApp()
