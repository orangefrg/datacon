from .linux_generic_selfdiag import LinuxSelfDiagProto
import sys, re, os, psutil
from datetime import datetime
import logging

class OrangePiSelfDiag(LinuxSelfDiagProto):

    def __init__(self, name, description, scheduler, broker="amqp", publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG):
            
        super().__init__(name, description, scheduler, broker, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)
        self.log_message("Initializing self-diagnostics for Orange Pi", logging.INFO)

# Overriding defaults

    def get_current_reading(self, src_id=None):
        reading = []
        reading.extend(self._get_cpu_usage())
        reading.extend(self._get_cpu_frequency())
        reading.extend(self._get_temperature("iio_hwmon", "SoC"))
        reading.extend(self._get_free_space())
        reading.extend(self._get_ram_usage())
        return reading
