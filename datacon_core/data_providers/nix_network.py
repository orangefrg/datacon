from .proto import Provider
import sys, re, os, psutil, socket
from datetime import datetime
import logging

class ConnectionMon(Provider):

    def __init__(self, name, description, scheduler, broker="amqp", publish_routing_key="all.all",
                 command_routing_keys=[], redis_channel="all", pass_to=None, loglevel=logging.DEBUG,
                 connection_filter={}):
        self._iface = connection_filter.get("iface")
        self._port = connection_filter.get("port")
        self._alias_conn = connection_filter.get("alias_conn")
        self._alias_if = connection_filter.get("alias_if")
        super().__init__(name, description, scheduler, broker, publish_routing_key,
                         command_routing_keys, redis_channel, pass_to, loglevel)
        self.log_message("Initializing network connection diagnostics", logging.INFO)

    def _check_iface_address(self):
        self._ip_addresses = []
        for name, settings in psutil.net_if_addrs().items():
            if self._iface is not None and self._iface != name:
                continue
            for s in settings:
                if s.family == socket.AF_INET:
                    self._ip_addresses.append(s.address)

    def _get_connection_stats(self):

        tag_name = self._alias_if or self._iface or "all"
        tag_subname = self._alias_conn or self._port or "all"
        connection_counter = { "name": "Network.{}".format(tag_name),
                "units": "",
                "measured_parameter": "connections_{}".format(tag_subname),
                "type": "Numeric",
                "reading": 0 }
        is_listening = { "name": "Network.{}".format(tag_name),
                "measured_parameter": "is_listening_{}".format(tag_subname),
                "type": "Discrete",
                "reading": False }
        ip_connected = { "name": "Network.{}".format(tag_name),
                "units": "",
                "measured_parameter": "clients_{}".format(tag_subname),
                "type": "Numeric",
                "reading": 0 }
        client_ips = []
        for conn in psutil.net_connections():
            laddr_fields = conn.laddr._fields
            if(type(conn.laddr) == psutil._common.addr and "port" in laddr_fields and "ip" in laddr_fields):
                port = conn.laddr.port
                addr = conn.laddr.ip
                port_pass = port == self._port or self._port is None
                ip_pass = addr in self._ip_addresses or len(self._ip_addresses) == 0
                if port_pass and ip_pass:
                    if conn.status == "ESTABLISHED":
                        connection_counter["reading"] += 1
                        if (type(conn.raddr) == psutil._common.addr and "ip" in conn.raddr._fields):
                            if conn.raddr.ip not in client_ips:
                                client_ips.append(conn.raddr.ip)
                    elif conn.status == "LISTEN":
                        is_listening["reading"] = True
        ip_connected["reading"] = len(client_ips)
        res_list = [connection_counter, is_listening, ip_connected]
        return res_list

# Overriding defaults

    def get_current_reading(self, src_id=None):
        self._check_iface_address()
        reading = self._get_connection_stats()
        return reading