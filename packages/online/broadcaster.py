import time
import requests
from dt_class_utils import DTProcess
from dt_service_utils import DTService


class GlobalBroadcaster:

    forget_location_after_mins = 60
    geolocation_timeout_secs = 5.0
    online_check_period_secs = 1.0 * 20.0
    broadcast_period_secs = 1.0 * 60.0
    heartbeat_hz = 1.0
    geolocation_app = "https://freegeoip.app/json/"

    def __init__(self):
        self.geodata = None
        self.last_broadcast = 0.0
        self.last_online_check = 0.0
        self.online = DTService('ONLINE', paused=True)

    def update(self):
        # perform geo-localization
        try:
            r = requests.get(self.geolocation_app, timeout=self.geolocation_timeout_secs)
            if r.status_code == 200:
                self.geodata = r.text.strip()
                self.last_online_check = time.time()
                # we were able to contact the remote API, the device is online
                self.online.yes()
            else:
                # we were NOT able to contact the remote API, the device is offline
                self.online.no()
        except requests.exceptions.RequestException:
            # something went wrong, let's assume that the device is offline
            self.online.no()
        # forget location
        location_age_secs = time.time() - self.last_online_check
        if location_age_secs >= self.forget_location_after_mins * 60:
            self.geodata = None

    def broadcast(self):
        if self.geodata:
            #TODO: this is where we transmit the data to the server
            print((self.geodata))
        self.last_broadcast = time.time()

    def start(self):
        while not DTProcess.get_instance().is_shutdown():
            # update location and opportunistically check if online
            if (time.time() - self.last_online_check) > self.online_check_period_secs:
                self.update()
            # broadcast geolocation to main server
            if (time.time() - self.last_broadcast) > self.broadcast_period_secs:
                self.broadcast()
            # keep the process alive
            time.sleep(1.0 / self.heartbeat_hz)
