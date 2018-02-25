from .linux_generic_selfdiag import LinuxSelfDiagProto
import logging

class VPSSelfDiag(LinuxSelfDiagProto):

    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG):
            
        super().__init__(name, description, scheduler, amqp, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)
        self.log_message("Initializing self-diagnostics for VPS", logging.INFO)

# Overriding defaults

    def get_current_reading(self, src_id=None):
        reading = []
        reading.extend(self._get_free_space())
        reading.extend(self._get_net_stats("ens3", "IP-1"))
        return reading