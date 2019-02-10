from .linux_generic_selfdiag import LinuxSelfDiagProto
import logging

class VPSSelfDiag(LinuxSelfDiagProto):

    def __init__(self, name, description, scheduler, broker="amqp", publish_routing_key="all.all",
                 command_routing_keys=[], redis_channel="all", pass_to=None, loglevel=logging.DEBUG,
                 if_name="lo", if_alias="localhost", free_space_path="/"):
        self._if_name = if_name
        self._if_alias = if_alias
        self._free_space_path = free_space_path
        super().__init__(name, description, scheduler, broker, publish_routing_key,
                         command_routing_keys, redis_channel, pass_to, loglevel)
        self.log_message("Initializing self-diagnostics for VPS", logging.INFO)

# Overriding defaults

    def get_current_reading(self, src_id=None):
        reading = []
        reading.extend(self._get_free_space(self._free_space_path))
        reading.extend(self._get_net_stats(self._if_name, self._if_alias))
        reading.extend(self._get_cpu_usage())
        reading.extend(self._get_ram_usage())
        return reading