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
DELAY_BACKUP_AFTER_START_SECS = 5


# Statistics collection for Duckietown
PROTOCOL_PORTS = {"http": 80, "https": 443}
# - defaults
DEFAULT_STATS_API_PROTOCOL = "https"
DEFAULT_STATS_API_HOSTNAME = "stats.duckietown.org"
DEFAULT_STATS_API_VERSION = "v2"
# - read from env
#   + protocol
STATS_API_PROTOCOL = os.environ.get("STATS_SERVER_PROTOCOL", default=DEFAULT_STATS_API_PROTOCOL)
if STATS_API_PROTOCOL != DEFAULT_STATS_API_PROTOCOL:
    print(f"NOTE: Using custom STATS_API_PROTOCOL={STATS_API_PROTOCOL}\n"
          f"      (default is {DEFAULT_STATS_API_PROTOCOL})")
#   + hostname
STATS_API_HOSTNAME = os.environ.get("STATS_SERVER_HOST", default=DEFAULT_STATS_API_HOSTNAME)
if STATS_API_HOSTNAME != DEFAULT_STATS_API_HOSTNAME:
    print(f"NOTE: Using custom STATS_API_HOSTNAME={STATS_API_HOSTNAME}\n"
          f"      (default is {DEFAULT_STATS_API_HOSTNAME})")
#   + port
DEFAULT_STATS_API_PORT = PROTOCOL_PORTS[STATS_API_PROTOCOL]
STATS_API_PORT = os.environ.get("STATS_SERVER_PORT", default=DEFAULT_STATS_API_PORT)
if STATS_API_PORT != DEFAULT_STATS_API_PORT:
    print(f"NOTE: Using custom STATS_API_PORT={STATS_API_PORT}\n"
          f"      (default is {DEFAULT_STATS_API_PORT})")
#   + version
STATS_API_VERSION = os.environ.get("STATS_SERVER_VERSION", default="v2")
if STATS_API_VERSION != DEFAULT_STATS_API_VERSION:
    print(f"NOTE: Using custom STATS_API_VERSION={STATS_API_VERSION}\n"
          f"      (default is {DEFAULT_STATS_API_VERSION})")
# compile URL
STATS_API_BASE_URL = f"{STATS_API_PROTOCOL}://{STATS_API_HOSTNAME}:{STATS_API_PORT}/{STATS_API_VERSION}"
STATS_API_URL = STATS_API_BASE_URL + "/{category}/{key}?" \
                                     "device={device}&boot_id={boot_id}&stamp={stamp}"
STATS_PUBLISHER_PERIOD_SECS = 30
STATS_BOOT_ID_FILE = "/proc/sys/kernel/random/boot_id"

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
