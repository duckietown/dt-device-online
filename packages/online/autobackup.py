import os
import time
from threading import Thread

import dt_data_api
from dt_class_utils import DTProcess
from dt_device_utils import get_device_id
from dt_device_utils.device import get_device_hostname
from dt_permissions_utils import permission_granted
from dt_secrets_utils import get_secret

from .constants import FILES_TO_BACKUP, REMOTE_BACKUP_LOCATION, BACKUP_BUCKET_NAME, \
    DELAY_BACKUP_AFTER_START_SECS


class AutoBackupWorker(Thread):

    def __init__(self):
        super().__init__()

    def run(self):
        app = DTProcess.get_instance()
        # (try to) read the token
        try:
            token = get_secret('tokens/dt1')
        except FileNotFoundError:
            # no token? nothing to do
            app.logger.warning('No secret token dt1 found. Cannot backup device.')
            return
        # read the permissions
        granted = permission_granted('allow_push_config_data')
        if not granted:
            app.logger.warning("Permission 'allow_push_config_data' not granted. Won't backup.")
            return
        # (try to) read the device ID
        try:
            device_id = get_device_id()
        except ValueError:
            # no device ID? nothing to do
            app.logger.warning("Could not find the device's unique ID. Cannot backup device.")
            return
        # prepare data for placeholders
        data = {
            'hostname': get_device_hostname()
        }
        # prepare list of files to upload
        to_upload = [f.format(**data) for f in FILES_TO_BACKUP]
        uploaded = set()
        missing = set()
        # spin up a Storage interface
        client = dt_data_api.DataClient(token)
        storage = client.storage(BACKUP_BUCKET_NAME)
        # try to upload the robot configuration
        while not app.is_shutdown():
            left_to_process = 0
            time.sleep(DELAY_BACKUP_AFTER_START_SECS)
            # go through the list of files to upload
            for local_filepath in to_upload:
                # make sure the app is still running
                if app.is_shutdown():
                    return
                # make sure the file hasn't been uploaded or blacklisted
                if local_filepath in uploaded or local_filepath in missing:
                    continue
                # make sure the file exists
                if not os.path.isfile(local_filepath):
                    missing.add(local_filepath)
                    continue
                left_to_process += 1
                # try uploading
                remote_filepath = REMOTE_BACKUP_LOCATION(device_id, local_filepath)
                handler = storage.upload(local_filepath, remote_filepath)
                handler.join()
                if handler.status == dt_data_api.TransferStatus.FINISHED:
                    app.logger.info(f"File '{local_filepath}' successfully backed up!")
                    uploaded.add(local_filepath)
                    left_to_process -= 1
                else:
                    app.logger.warning(f"Backup of file '{local_filepath}' ended with "
                                       f"status {handler.status.name}, reason: {handler.reason}")
            # if we uploaded everything, you can stop
            if left_to_process == 0:
                app.logger.info(f"Files backup completed!")
                break
            # retry every 60 seconds
            time.sleep(60)
