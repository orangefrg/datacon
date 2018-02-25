from .linux_generic_selfdiag import LinuxSelfDiagProto
from datetime import datetime

class VPSSelfDiag(LinuxSelfDiagProto):

    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG):
            
        super().__init__(name, description, scheduler, amqp, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)
        self.log_message("Initializing self-diagnostics for Orange Pi", logging.INFO)

# Overriding defaults

    def get_current_reading(self, src_id=None):
        reading = {}
        reading["name"] = self._name
        reading["start_time"] = datetime.datetime.utcnow().isoformat()

        rdng = []
        rdng = self._get_cpu_usage(rdng)
        rdng = self._get_temperature(rdng, "iio_hwmon", "SoC")
        rdng = self._get_free_space(rdng)
        rdng = self._get_ram_usage(rdng)
        reading["reading"] = rdng
                 
        reading["end_time"] = datetime.datetime.utcnow().isoformat()
        return reading