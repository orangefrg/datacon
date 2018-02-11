from .proto import Provider
import sys, re, os
import datetime


class Ds18b20(Provider):
    DALLAS_BASE_DIR = '/sys/bus/w1/devices/'

    def _get_sensor_by_id(self, sensor_id):
        for s in self._sensors:
            if s["id"] == sensor_id:
                return s
        return None

    def _add_sensor(self, sensor_id):
        sens = {"id": sensor_id,
                "full_path": self.DALLAS_BASE_DIR + sensor_id + "/w1_slave"}
        if sensor_id in self._sensor_aliases:
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


    def __init__(self, name, description, scheduler=None, sensor_aliases={}):
        self._sensors = []
        self._sensor_aliases = sensor_aliases
        
        self._crc_re = re.compile("(YES|NO)")
        self._temp_re = re.compile("t=(([-]*)(\d+))")

        self._refresh_sensors_list()
        super().__init__(name, description, scheduler)


# Overriding defaults

    def get_current_reading(self, src_id=None):
        reading = {}
        reading["name"] = self._name
        reading["start_time"] = datetime.datetime.utcnow().isoformat()
        reading["reading"] = []

        for s in self._sensors:
            current = {}
            if "alias" in s:
                current["name"] = s["alias"]
            else:
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
                current["error"] = "Reading error"
            elif not crc:
                current["error"] = "CRC error"
            else:
                current["reading"] = temp
                current["units"] = "°C"
                current["measured_parameter"] = "temperature"
            reading["reading"].append(current)
        reading["end_time"] = datetime.datetime.utcnow().isoformat()
        return reading

