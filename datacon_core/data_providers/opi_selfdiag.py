from .proto import Provider
import sys, re, os, psutil
import datetime
import logging

class OrangePiSelfDiag(Provider):

    soc_temp_file = "/etc/armbianmonitor/datasources/soctemp"
    root_partition = "/"

    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG):
        self._total_re = re.compile("MemTotal:(.*?)(\d+)")
        self._free_re = re.compile("MemFree:(.*?)(\d+)")
        super().__init__(name, description, scheduler, amqp, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)
        self.log_message("Initializing self-diagnostics for Orange Pi", logging.INFO)

    def _get_soc_temp(self, res_list):
        self.log_message("Getting Soc temperature", logging.DEBUG)
        tmp = { "name": "SoC",
                "units": "°C",
                "measured_parameter": "temperature"}
        try:
            with open(self.soc_temp_file) as f:
                tmp["reading"] = float(f.readline())/1000
        except:
            self.log_message("Could not get SoC temperature: {}".format(sys.exc_info()[0]), logging.ERROR)
            tmp["error"] = "Reading error"
        res_list.append(tmp)
        return res_list

    def _get_free_space(self, res_list):
        self.log_message("Getting free space on disk", logging.DEBUG)
        f_gb = {"name": "/",
                "units": "Mb",
                "measured_parameter": "free"}
        t_gb = {"name": "/",
                "units": "Mb",
                "measured_parameter": "total"}
        try:
            vfs = os.statvfs("/")
            free_gb = float(vfs.f_bsize * vfs.f_bfree) / 1048576
            total_gb = float(vfs.f_frsize * vfs.f_blocks) / 1048576
            f_gb["reading"] = free_gb
            t_gb["reading"] = total_gb
        except:
            self.log_message("Could not get free space on disk: {}".format(sys.exc_info()[0]), logging.ERROR)
            f_gb["error"] = "Reading error"
            t_gb["error"] = "Reading error"
        res_list.append(f_gb)
        res_list.append(t_gb)
        return res_list

    def _get_ram_usage(self, res_list):
        self.log_message("Getting RAM usage", logging.DEBUG)
        f_ram = {"name": "RAM",
                "units": "Mb",
                "measured_parameter": "free"}
        t_ram = {"name": "RAM",
                "units": "Mb",
                "measured_parameter": "total"}
        matches = 0
        with open("/proc/meminfo") as f:
            for l in f.readlines():
                total_m = self._total_re.match(l)
                free_m = self._free_re.match(l)
                if total_m:
                    matches += 1
                    t_ram["reading"] = float(total_m.group(2)) / 1024
                elif free_m:
                    matches += 1
                    f_ram["reading"] = float(free_m.group(2)) / 1024
                if matches >= 2:
                    break
            for rd in [t_ram, f_ram]:
                if "reading" not in rd:
                    self.log_message("Could not get RAM usage", logging.ERROR)
                    rd["error"] = "Reading error"
        res_list.append(t_ram)
        res_list.append(f_ram)
        return res_list

    def _get_cpu_usage(self, res_list):
        self.log_message("Getting CPU usage", logging.DEBUG)
        cpu_l = {
            "name": "CPU",
            "measured_parameter": "load",
            "units": "%"
        }
        cpu_f = {
            "name": "CPU",
            "measured_parameter": "frequency",
            "units": "MHz"
        }
        try:
            cpu_l["reading"] = psutil.cpu_percent(interval=0.1)
        except:
            self.log_message("Could not get CPU load: {}".format(sys.exc_info()[0]), logging.ERROR)
            cpu_l["error"] = "reading error"
        try:
            cpu_f["reading"] = psutil.cpu_freq().current
        except:
            self.log_message("Could not get CPU frequency: {}".format(sys.exc_info()[0]), logging.ERROR)
            cpu_f["error"] = "reading error"
        res_list.append(cpu_l)
        res_list.append(cpu_f)
        return res_list


# Overriding defaults

    def get_current_reading(self, src_id=None):
        reading = {}
        reading["name"] = self._name
        reading["start_time"] = datetime.datetime.utcnow().isoformat()

        rdng = []
        rdng = self._get_cpu_usage(rdng)
        rdng = self._get_soc_temp(rdng)
        rdng = self._get_free_space(rdng)
        rdng = self._get_ram_usage(rdng)
        reading["reading"] = rdng
                 
        reading["end_time"] = datetime.datetime.utcnow().isoformat()
        return reading
