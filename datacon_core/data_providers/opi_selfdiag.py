from .proto import Provider
import sys, re, os
import datetime

class OrangePiSelfDiag(Provider):

    def __init__(self, name, description, sensor_aliases={}):
        self._name = name
        self._description = description
        self._sensors = []
        self._sensor_aliases = sensor_aliases
        
        self._crc_re = re.compile("(YES|NO)")
        self._temp_re = re.compile("t=(([-]*)(\d+))")



# Overriding defaults

    def get_name(self):
        return self._name
    def get_measured_parameter(self):
        return "temperature"
    def get_description(self):
        return self._description
    def get_current_reading(self, src_id=None):
        reading = {}
        reading["name"] = self._name
        reading["start_time"] = datetime.datetime.utcnow().isoformat()
        reading["reading"] = []
        # TODO: Temperature, CPU load, RAM, network, free space on disks

        reading["end_time"] = datetime.datetime.utcnow().isoformat()
        return reading

    # Activate and deactivate scheduled data retrieval
    # time_settings is a dict with following fields:
    # type (required): 'interval' or 'schedule'
    # interval (if interval): interval in seconds (integer)
    # schedule (if schedule): list of tuples (hour, minute, second)
    def activate_polling(self, time_settings):
        raise NotImplementedError
    def deactivate_polling(self):
        raise NotImplementedError

    def set_parameter(self, parameter_name, parameter_value):
        raise NotImplementedError
    def get_parameter(self, parameter_name):
        raise NotImplementedError