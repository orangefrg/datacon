from .proto import Provider
from random import randint
import datetime
import logging
import sys

HEARTBEAT_UPPER_LIMIT = 4096

class Heartbeat(Provider):
    def __init__(self, name, description, scheduler, broker="amqp", publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG):
        self._counter = 0
        self._increment = True
        super().__init__(name, description, scheduler, broker, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)
        self.log_message("Starting heartbeat", logging.INFO)

    def get_current_reading(self, src_id=None):
        reading = []

        self.log_message("Generating counter", logging.DEBUG)
        reading.append({
            "name": "test",
            "units": "",
            "measured_parameter": "counter",
            "reading": self._counter,
            "type": "Numeric"
        })

        self.log_message("Generating random", logging.DEBUG)
        reading.append({
            "name": "test",
            "units": "",
            "measured_parameter": "random",
            "reading": randint(0, HEARTBEAT_UPPER_LIMIT),
            "type": "Numeric"
        })

        if self._counter >= HEARTBEAT_UPPER_LIMIT:
            self._increment = False
        elif self._counter <= 0:
            self._increment = True
        if self._increment:
            self._counter += 1
        else:
            self._counter -=1
        return reading