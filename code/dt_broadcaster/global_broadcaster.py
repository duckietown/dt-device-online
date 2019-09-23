import os
import time
import requests
from dt_class_utils import DTProcess

class GlobalBroadcaster(DTProcess):

    token = "null"
    geodata = None
    location_age_secs = 0.0
    location_last_update = 0.0
    forget_location_after_mins = 60
    geolocation_timeout_secs = 5.0
    broadcast_period_secs = 10.0
    hearthbeat_hz = 1.0
    protocol = "https"
    host = "dashboard.duckietown.org"
    api_version = "1.0"
    uri = "web-api/{api_version}/{service}/{action}?{qs}"
    geolocation_app = "https://freegeoip.app/json/"
    token_file = '/secrets/tokens/dt1'

    def __init__(self):
        DTProcess.__init__(self)
        # update
        self.last_broadcast = 0.0
        self.location_last_update = time.time()
        self.update()

    def update(self):
        # read dt-token
        if os.path.exists(self.token_file):
            with open(self.token_file) as fin:
                self.token = fin.read().decode('utf-8').strip()
        # perform geo-localization
        try:
            r = requests.get(self.geolocation_app, timeout=self.geolocation_timeout_secs)
            if r.status_code == 200:
                self.geodata = r.text.strip()
                self.location_last_update = time.time()
        except:
            pass
        self.location_age_secs = time.time() - self.location_last_update
        # forget location
        if self.location_age_secs >= self.forget_location_after_mins * 60:
            self.geodata = None

    def broadcast(self):
        if self.geodata:
            print(self.geodata)
        self.last_broadcast = time.time()

    def start(self):
        while not self.is_shutdown:
            # broadcast (if needed)
            if time.time() - self.last_broadcast > self.broadcast_period_secs:
                self.update()
                self.broadcast()
            # keep the process alive
            time.sleep(1.0 / self.hearthbeat_hz)
