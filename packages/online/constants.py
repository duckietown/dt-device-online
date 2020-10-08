import os

REMOTE_BACKUP_LOCATION = lambda user_id, device, key: os.path.join(
    'user', user_id, 'device', device, 'backup', key[1:] if key.startswith('/') else key)

FILES_TO_BACKUP = [
    '/data/config/calibrations/camera_extrinsic/{hostname}.yaml',
    '/data/config/calibrations/camera_intrinsic/{hostname}.yaml',
    '/data/config/calibrations/kinematics/{hostname}.yaml',
]

BACKUP_BUCKET_NAME = 'private'

DELAY_BACKUP_AFTER_START_SECS = 4
