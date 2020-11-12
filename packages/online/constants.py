import os

BACKUP_BUCKET_NAME = 'user'

REMOTE_BACKUP_LOCATION = lambda user_id, device, key: \
    os.path.join(str(user_id), 'device', device, 'backup', key.lstrip('/'))

FILES_TO_BACKUP = [
    '/data/config/calibrations/camera_extrinsic/{hostname}.yaml',
    '/data/config/calibrations/camera_intrinsic/{hostname}.yaml',
    '/data/config/calibrations/kinematics/{hostname}.yaml',
]

DELAY_BACKUP_AFTER_START_SECS = 4
