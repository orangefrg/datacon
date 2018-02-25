from .proto import Provider
import sys, re, os
import datetime
import logging


class Ds18b20(Provider):
    DALLAS_BASE_DIR = '/sys/bus/w1/devices/'

    def _get_sensor_by_id(self, sensor_id):
        for s in self._sensors:
            if s["id"] == sensor_id:
                return s
        return None

    def _add_sensor(self, sensor_id):
        self.log_message("Adding sensor {}".format(sensor_id), logging.INFO)
        sens = {"id": sensor_id,
                "full_path": self.DALLAS_BASE_DIR + sensor_id + "/w1_slave"}
        if sensor_id in self._sensor_aliases:
            self.log_message("Sensor {} has alias {}".format(sensor_id, self._sensor_aliases[sensor_id]), logging.DEBUG)
            sens["alias"] = self._sensor_aliases[sensor_id]
        sens["added"] = datetime.datetime.utcnow().isoformat()
        sens["updated"] = datetime.datetime.utcnow().isoformat()
        sens["error_count"] = 0
        self._sensors.append(sens)

    def _refresh_sensors_list(self):
        for f in os.listdir(self.DALLAS_BASE_DIR):
            if re.match("28(.*)", f):
                if self._get_sensor_by_id(f) is None:
                    self._add_sensor(f)


    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG, sensor_aliases={}):
        self._sensors = []
        self._sensor_aliases = sensor_aliases
        
        self._crc_re = re.compile("(YES|NO)")
        self._temp_re = re.compile("t=(([-]*)(\d+))")

        super().__init__(name, description, scheduler, amqp, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)
        self._refresh_sensors_list()


# Overriding defaults

    def get_current_reading(self, src_id=None):
        self.log_message("Querying sensors via 1-wire bus", logging.DEBUG)
        reading = []
        for s in self._sensors:
            try:
                current = {}
                if "alias" in s:
                    self.log_message("Querying {} ({})".format(s["alias"], s["id"]), logging.DEBUG)
                    current["name"] = s["alias"]
                else:
                    self.log_message("Querying {}".format(s["id"]), logging.DEBUG)
                    current["name"] = s["id"]
                with open(s["full_path"]) as sensor_file:
                    readings = sensor_file.readlines()
                for r in readings:
                    crc_match = self._crc_re.search(r)
                    temp_match = self._temp_re.search(r)
                    if crc_match:
                        crc = crc_match.group(1) == "YES"
                    elif temp_match:
                        temp = float(temp_match.group(1))/1000
                if temp is None or crc is None:
                    self.log_message("Reading error for {}".format(current["name"]), logging.WARNING)
                    current["error"] = "Reading error"
                elif not crc:
                    self.log_message("CRC error for {}".format(current["name"]), logging.WARNING)
                    current["error"] = "CRC error"
                else:
                    current["reading"] = temp
                    current["units"] = "°C"
                    current["measured_parameter"] = "temperature"
                reading.append(current)
            except:
                self.log_message("Error querying sensors: {}".format(sys.exc_info()[0]), logging.ERROR)   
        return reading

