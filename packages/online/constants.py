import os

REMOTE_BACKUP_LOCATION = lambda device, key: \
    os.path.join('device', device, 'backup', key[1:] if key.startswith('/') else key)
FILES_TO_BACKUP = [
    '/data/config/calibrations/camera_extrinsic/{hostname}.yaml',
    '/data/config/calibrations/camera_intrinsic/{hostname}.yaml',
    '/data/config/calibrations/kinematics/{hostname}.yaml',
]
BACKUP_BUCKET_NAME = 'public'
DELAY_BACKUP_AFTER_START_SECS = 4
