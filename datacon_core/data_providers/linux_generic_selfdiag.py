from .proto import Provider
import re, os, logging, psutil, sys, socket

class LinuxSelfDiagProto(Provider):

    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG):
        super().__init__(name, description, scheduler, amqp, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)

    def _get_free_space(self, path="/"):
        res_list = []
        self.log_message("Getting free space on disk", logging.DEBUG)
        f_gb = {"name": path,
                "units": "Mb",
                "measured_parameter": "free",
                "type": "Numeric"}
        t_gb = {"name": path,
                "units": "Mb",
                "measured_parameter": "total",
                "type": "Numeric"}
        try:
            p = psutil.disk_usage(path)
            free_gb = (p.total - p.used) / 1048576.0
            total_gb = p.total / 1048576.0
            f_gb["reading"] = free_gb
            t_gb["reading"] = total_gb
        except:
            self.log_message("Could not get free space on disk: {}".format(sys.exc_info()[0]), logging.ERROR)
            f_gb["error"] = "Reading error"
            t_gb["error"] = "Reading error"
        res_list.append(f_gb)
        res_list.append(t_gb)
        return res_list

    def _get_ram_usage(self):
        res_list = []
        self.log_message("Getting RAM usage", logging.DEBUG)
        f_ram = {"name": "RAM",
                "units": "Mb",
                "measured_parameter": "free",
                "type": "Numeric"}
        t_ram = {"name": "RAM",
                "units": "Mb",
                "measured_parameter": "total",
                "type": "Numeric"}
        matches = 0
        mem = psutil.virtual_memory()
        try:
            t_ram["reading"] = mem.total / 1048576.0
            f_ram["reading"] = mem.available / 1048576.0
        except:
            for rd in [t_ram, f_ram]:
                if "reading" not in rd:
                    self.log_message("Could not get RAM usage", logging.ERROR)
                    rd["error"] = "Reading error"
        res_list.append(t_ram)
        res_list.append(f_ram)
        return res_list

    def _get_cpu_usage(self):
        res_list = []
        self.log_message("Getting CPU usage", logging.DEBUG)
        cpu_l = {
            "name": "CPU",
            "measured_parameter": "load",
            "units": "%",
            "type": "Numeric"
        }
        try:
            cpu_l["reading"] = psutil.cpu_percent(interval=0.1)
        except:
            self.log_message("Could not get CPU load: {}".format(sys.exc_info()[0]), logging.ERROR)
            cpu_l["error"] = "reading error"
        res_list.append(cpu_l)
        return res_list

    def _get_cpu_frequency(self):
        res_list = []
        self.log_message("Getting CPU frequency", logging.DEBUG)
        cpu_f = {
            "name": "CPU",
            "measured_parameter": "frequency",
            "units": "MHz",
            "type": "Numeric"
        }
        try:
            cpu_f["reading"] = psutil.cpu_freq().current
        except:
            self.log_message("Could not get CPU frequency: {}".format(sys.exc_info()[0]), logging.ERROR)
            cpu_f["error"] = "reading error"
        res_list.append(cpu_f)
        return res_list

    def _get_temperature(self, sensor_id, sensor_name=None):
        res_list = []
        if sensor_name is None:
            sensor_name = sensor_id
        self.log_message("Getting {} temperature".format(sensor_name), logging.DEBUG)
        tmp = { "name": sensor_name,
                "units": "°C",
                "measured_parameter": "temperature",
                "type": "Numeric"}
        try:
            tmp_value = psutil.sensors_temperatures()[sensor_id][0].current
            tmp["reading"] = tmp_value
        except:
            self.log_message("Could not get {} temperature: {}".format(sensor_name, sys.exc_info()[0]), logging.ERROR)
            tmp["error"] = "Reading error"
        res_list.append(tmp)
        return res_list

    def _get_net_stats(self, if_id, if_name=None, get_bytes=True, get_errors=True):
        res_list = []
        if if_name is None:
            if_name = if_id
        self.log_message("Getting network interface {} statistics".format(if_name), logging.DEBUG)
        if get_bytes:
            bytes_rx = { "name": "Network.{}".format(if_name),
                    "units": "Mb",
                    "measured_parameter": "traffic_in",
                    "type": "Numeric"}
            bytes_tx = { "name": "Network.{}".format(if_name),
                    "units": "Mb",
                    "measured_parameter": "traffic_out",
                    "type": "Numeric"}
            res_list.append(bytes_rx)
            res_list.append(bytes_tx)
        if get_errors:
            err_rx = { "name": "Network.{}".format(if_name),
                    "units": "",
                    "measured_parameter": "errors_in",
                    "type": "Numeric"}
            err_tx = { "name": "Network.{}".format(if_name),
                    "units": "",
                    "measured_parameter": "errors_out",
                    "type": "Numeric"}
            res_list.append(err_rx)
            res_list.append(err_tx)
        ip_v4 = { "name": "Network.{}".format(if_name),
                "units": "",
                "measured_parameter": "address_ip4",
                "type": "Text"}
        mac = { "name": "Network.{}".format(if_name),
                "units": "",
                "measured_parameter": "address_mac",
                "type": "Text"}
        res_list.append(ip_v4)
        res_list.append(mac)
        addr = psutil.net_if_addrs()
        if if_id not in addr:
            ip_v4["error"] = "Interface not found"
            mac["error"] = "Interface not found"
            stats = []
        else:
            if_addr = addr[if_id]
            ip_v4["reading"] = "None"
            mac["reading"] = "None"
            for i in if_addr:
                if i.family == socket.AF_INET:
                    ip_v4["reading"] = i.address
                    continue
                if i.family == psutil.AF_LINK:
                    mac["reading"] = i.address
                    continue
        if get_bytes or get_errors:
            stats = psutil.net_io_counters(pernic=True)
            if get_bytes:
                try:
                    if if_id not in stats:
                        for t in [bytes_rx, bytes_tx]:
                            t["error"] = "Interface not found"
                            res_list.append(t)
                    bytes_rx["reading"] = stats[if_id].bytes_recv / 1048576.0
                    bytes_tx["reading"] = stats[if_id].bytes_sent / 1048576.0
                except:
                    for t in [bytes_rx, bytes_tx]:
                        t["error"] = "Error getting stats"
                        res_list.append(t)
            if get_errors:
                try:
                    if if_id not in stats:
                        for t in [err_rx, err_tx]:
                            t["error"] = "Interface not found"
                            res_list.append(t)
                    err_rx["reading"] = stats[if_id].errin
                    err_tx["reading"] = stats[if_id].errout
                except:
                    for t in [err_rx, err_tx]:
                        t["error"] = "Error getting stats"
        return res_list


        



