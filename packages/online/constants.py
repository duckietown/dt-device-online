import os


# Auto-Backup of files to the DCSS
BACKUP_BUCKET_NAME = 'user'
REMOTE_BACKUP_LOCATION = lambda user_id, device, key: \
    os.path.join(str(user_id), 'device', device, 'backup', key.lstrip('/'))
FILES_TO_BACKUP = [
    '/data/config/calibrations/camera_extrinsic/{hostname}.yaml',
    '/data/config/calibrations/camera_intrinsic/{hostname}.yaml',
    '/data/config/calibrations/kinematics/{hostname}.yaml',
]
DELAY_BACKUP_AFTER_START_SECS = 4


# Statistics collection for Duckietown
STATS_API_HOSTNAME = "stats.duckietown.org"
STATS_API_VERSION = "v1"
STATS_API_VERB = "POST"
STATS_API_BASE_URL = "https://{STATS_API_HOSTNAME}/{STATS_API_VERSION}"
STATS_API_URL = STATS_API_BASE_URL + "/{category}?"
STATS_PUBLISHER_PERIOD = 8

STATS_CATEGORY_TO_DIR = {
    "event": "/data/stats/events",
    "usage": "/data/stats/usage"
}


class FREQUENCY:
    ONESHOT = 0
    EVERY_5_SECONDS = 1.0 / 5
    EVERY_10_SECONDS = 1.0 / 10
    EVERY_30_SECONDS = 1.0 / 30
    EVERY_MINUTE = 1.0 / (60 * 1)
    EVERY_2_MINUTES = 1.0 / (60 * 2)
    EVERY_5_MINUTES = 1.0 / (60 * 5)
    EVERY_10_MINUTES = 1.0 / (60 * 10)
    EVERY_30_MINUTES = 1.0 / (60 * 30)
    EVERY_1_HOUR = 1.0 / (60 * 60 * 1)
    EVERY_2_HOURS = 1.0 / (60 * 60 * 1)
