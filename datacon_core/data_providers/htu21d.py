from .proto import Provider
from smbus2 import SMBus
import datetime
from math import log, fabs
import logging
import sys

class HTU21D(Provider):
    SLAVE_ADDRESS = 0x40

    READ_TEMPERATURE_COMMAND = 0xE3
    READ_HUMIDITY_COMMAND = 0xE5

    READ_USER_REGISTER_COMMAND = 0xE7
    WRITE_USER_REGISTER_COMMAND = 0xE6

    DEFAULT_SETTINGS = 0x02
    HEATER_BIT = 2

    SOFT_RESET_COMMAND = 0xFE

    # Heater enables periodically at temperatures near dewpoint (abs(T - Tp)<=DEWPOINT_DELTA)
    # Upon reaching trigger temperature, heater enables
    # HEATER_OPERATION decrements every measurement cycle
    # Upon reaching zero, heater is turned off
    # After that, cooldown timer decrements
    # Upon reaching zero, heater is re-enabled
    DEWPOINT_DELTA = 1
    HEATER_COOLDOWN = 10
    HEATER_OPERATION = 5

    # TODO:
    # CRC-8 check

    def _get_temperature(self):
        out_temp = {"name": "Main",
                    "measured_parameter": "temperature",
                    "units": "°C"}
        try:
            self.log_message("Reading temperature", logging.DEBUG)  
            msb, lsb, crc = self._bus.read_i2c_block_data(self.SLAVE_ADDRESS, self.READ_TEMPERATURE_COMMAND ,3)
            temp = -46.85 + 175.72 * (msb * 256 + lsb) / 65536.0
            out_temp["reading"] = temp
            self._last_temperature = temp
            self._temperature_ok = True
        except:
            self.log_message("Could not read temperature: {}".format(sys.exc_info()[0]), logging.ERROR)
            out_temp["error"] = "Reading error"
            self._temperature_ok = False
        return out_temp

    def _get_humidity(self):
        out_hum = {"name": "Main",
                    "measured_parameter": "humidity",
                    "units": "%"}
        try:
            self.log_message("Reading humidity", logging.DEBUG)  
            msb, lsb, crc = self._bus.read_i2c_block_data(self.SLAVE_ADDRESS, self.READ_HUMIDITY_COMMAND ,3)
            hum = -6 + 125 * (msb * 256 + lsb) / 65536.0
            out_hum["reading"] = hum
            self._last_humidity = hum
            self._humidity_ok = True
        except:
            self.log_message("Could not read humidity: {}".format(sys.exc_info()[0]), logging.ERROR)
            out_hum["error"] = "Reading error"
            self._humidity_ok = False
        return out_hum

    def _dew_control(self):
        self._dewpoint_reached = fabs(self._last_temperature - self._dewpoint) <= self.DEWPOINT_DELTA

    def _get_dewpoint(self):
        out_dew = {"name": "Dewpoint",
                   "measured_parameter": "temperature",
                   "units": "°C"}
        if self._last_humidity is None or self._last_temperature is None:
            self.log_message("Could not calculate dewpoint: No data", logging.DEBUG)  
            out_dew["error"] = "No input data"
        elif not self._temperature_ok or not self._humidity_ok:
            self.log_message("Could not calculate dewpoint: data is obsolete", logging.DEBUG)  
            out_dew["error"] = "Obsolete input data"
        else:
            try:
                self.log_message("Input data OK, going to calculate dewpoint", logging.DEBUG)  
                t = self._last_temperature
                rh = self._last_humidity
                dewpoint_gamma = 17.27 * t / (237.7 + t) + log(rh)
                dewpoint = 17.27 * dewpoint_gamma / (237.7 - dewpoint_gamma)
                out_dew["reading"] = dewpoint
                self._dewpoint = dewpoint
                self._dew_control()
            except:
                self.log_message("Could not calculate dewpoint: {}".format(sys.exc_info()[0]), logging.ERROR)
                out_dew["error"] = "Calculation error"
        return out_dew


    def _get_user_register_as_list(self):
        self.log_message("Reading user register", logging.DEBUG)  
        user_reg = self._bus.read_i2c_block_data(self.SLAVE_ADDRESS, self.READ_USER_REGISTER_COMMAND, 1)[0]
        return list(bin(user_reg)[2:].zfill(8))

    def _get_heater(self):
        out_heater = {"name": "Heater",
                      "measured_parameter": "status",
                      "units": ""}
        try:
            self.log_message("Getting heater status", logging.DEBUG)  
            out_heater["reading"] = self._get_user_register_as_list()[-3] == "1"
            self._heater_status = out_heater["reading"]
        except:
            self.log_message("Could not get heater status: {}".format(sys.exc_info()[0]), logging.ERROR)
            out_heater["error"] = "Reading error"
        return out_heater


    def _enable_heating(self):
        current_register = self._get_user_register_as_list()
        if current_register[-3] != "1":
            current_register[-3] = "1"
            self._bus.write_i2c_block_data(self.SLAVE_ADDRESS, self.WRITE_USER_REGISTER_COMMAND, [int("".join(current_register), 2)])
            return True
        else:
            return False

    def _disable_heating(self):
        current_register = self._get_user_register_as_list()
        if current_register[-3] != "0":
            current_register[-3] = "0"
            self._bus.write_i2c_block_data(self.SLAVE_ADDRESS, self.WRITE_USER_REGISTER_COMMAND, [int("".join(current_register), 2)])
            return True
        else:
            return False

    def _heater_control(self):
        if self._dewpoint_reached:
            self.log_message("Dewpoint reached, processing heater schedule", logging.DEBUG)  
            if self._heater_operation == 0 and self._heater_status:
                self.log_message("Disabling heater", logging.INFO)  
                self._disable_heating()
                self._heater_operation = self.HEATER_OPERATION
            elif self._heater_cooldown == 0 and not self._heater_status:
                self.log_message("Enabling heater", logging.INFO)  
                self._enable_heating()
                self._heater_cooldown = self.HEATER_COOLDOWN
            if self._heater_status:
                self._heater_operation -= 1
            else:
                self._heater_cooldown -= 1
        else:
            if self._heater_status:
                self.log_message("Disabling heater", logging.INFO)  
                self._disable_heating()
            self._heater_cooldown = self.HEATER_COOLDOWN
            self._heater_operation = self.HEATER_OPERATION


    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG, bus_number=0):
        super().__init__(name, description, scheduler, amqp, publish_routing_key,
                         command_routing_keys, pass_to, loglevel)
        self.log_message("Initializing I2C bus", logging.INFO)
        try:
            self._bus = SMBus(bus_number)
            self._heater_operation = self.HEATER_OPERATION
            self._heater_cooldown = self.HEATER_COOLDOWN
        except:
            self.log_message("I2C bus init failed: {}".format(sys.exc_info()[0]), logging.ERROR)


# Overriding defaults

    def get_current_reading(self, src_id=None):
        self.log_message("Reading values via I2C bus",logging.DEBUG)     
        reading = {}
        reading["name"] = self._name
        reading["start_time"] = datetime.datetime.utcnow().isoformat()
        reading["reading"] = []
        temp = self._get_temperature()
        hum = self._get_humidity()
        heater = self._get_heater()
        dewpoint = self._get_dewpoint()
        self.log_message("Checking dewpoint",logging.DEBUG)    
        self._heater_control()
        reading["reading"] = [temp, hum, heater, dewpoint]
        reading["end_time"] = datetime.datetime.utcnow().isoformat()
        return reading
