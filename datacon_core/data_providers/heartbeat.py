from .proto import Provider
from random import randint
import datetime

HEARTBEAT_UPPER_LIMIT = 4096

class Heartbeat(Provider):
    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None):
        self._counter = 0
        self._increment = True
        super().__init__(name, description, scheduler, amqp, publish_routing_key,
                         command_routing_keys, pass_to)

    def get_current_reading(self, src_id=None):
        reading = {}
        reading["name"] = self._name
        reading["start_time"] = datetime.datetime.utcnow().isoformat()
        reading["reading"] = []

        reading["reading"].append({
            "name": "test",
            "units": "",
            "measured_parameter": "counter",
            "reading": self._counter
        })

        reading["reading"].append({
            "name": "test",
            "units": "",
            "measured_parameter": "random",
            "reading": randint(0, HEARTBEAT_UPPER_LIMIT)
        })

        if self._counter >= HEARTBEAT_UPPER_LIMIT:
            self._increment = False
        elif self._counter <= 0:
            self._increment = True
        if self._increment:
            self._counter += 1
        else:
            self._counter -=1

        reading["end_time"] = datetime.datetime.utcnow().isoformat()
        return reading