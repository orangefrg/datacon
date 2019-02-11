from .proto import Provider
from smbus2 import SMBus
from math import log, fabs
import logging
import time
import sys

class BME280(Provider):

    DEFAULT_ADDRESS = 0x76

    OVERSAMPLING_1 = 1
    OVERSAMPLING_2 = 2
    OVERSAMPLING_4 = 3
    OVERSAMPLING_8 = 4
    OVERSAMPLING_16 = 5

    STANDBY_0p5 = 0
    STANDBY_62p5 = 1
    STANDBY_125 = 2
    STANDBY_250 = 3
    STANDBY_500 = 4
    STANDBY_1000 = 5
    STANDBY_10 = 6
    STANDBY_20 = 7

    FILTER_0 = 0
    FILTER_2 = 1
    FILTER_4 = 2
    FILTER_8 = 3
    FILTER_16 = 4

    MODE_SLEEP = 0x00
    MODE_FORCED = 0x01
    MODE_NORMAL = 0x03

    CALIBRATION_1_START = 0x88
    CALIBRATION_1_LENGTH = 24
    CALIBRATION_1_TAIL = 0xA1
    CALIBRATION_2_START = 0xE1
    CALIBRATION_2_LENGTH = 7

    ADDRESS_CHIPID = 0xD0
    ADDRESS_VERSION = 0xD1
    ADDRESS_SOFTRESET = 0xE0

    ADDRESS_STATUS = 0xF3
    ADDRESS_CONTROL_HUM = 0xF2
    ADDRESS_CONTROL = 0xF4
    ADDRESS_CONFIG = 0xF5
    ADDRESS_DATA = 0xF7

    DATA_LENGTH = 8

    def __init__(self, name, description, scheduler, broker="amqp", publish_routing_key="all.all",
                 command_routing_keys=[], redis_channel="all", pass_to=None, loglevel=logging.DEBUG, bus_number=0,
                 address=DEFAULT_ADDRESS, standby=STANDBY_125, forced_mode=False,
                 p_os=OVERSAMPLING_4, t_os=OVERSAMPLING_4, h_os=OVERSAMPLING_2, iir_filter=FILTER_2):
        super().__init__(name, description, scheduler, broker, publish_routing_key,
                         command_routing_keys, redis_channel, pass_to, loglevel)
        self.log_message("Initializing I2C bus", logging.INFO)
        try:
            self.bus = SMBus(bus_number)
            self.p_os = p_os
            self.t_os = t_os
            self.h_os = h_os
            self.iir_filter = iir_filter
            self.address = address
            self.forced_mode = forced_mode
            self.standby = standby
            self.mode = self.MODE_SLEEP if forced_mode else self.MODE_NORMAL

            self.log_message("Initializing BME280 and loading calibration",logging.DEBUG) 
            self._get_chip_id()
            self._get_calibration()

            self.log_message("Setting up BME280",logging.DEBUG) 
            self._upload_settings_hum()
            self._upload_settings_measurement()
            self._upload_settings_config()

        except:
            self.log_message("I2C bus init failed: {}".format(sys.exc_info()[0]), logging.ERROR)

    def _get_calibration(self):
        calibration = self.bus.read_i2c_block_data(self.address, self.CALIBRATION_1_START, self.CALIBRATION_1_LENGTH)
        calibration.append(self.bus.read_byte_data(self.address, self.CALIBRATION_1_TAIL))
        calibration.extend(self.bus.read_i2c_block_data(self.address, self.CALIBRATION_2_START, self.CALIBRATION_2_LENGTH))

        self.digT = []
        self.digT.append((calibration[1] << 8) | calibration[0])
        self.digT.append((calibration[3] << 8) | calibration[2])
        self.digT.append((calibration[5] << 8) | calibration[4])

        self.digP = []
        self.digP.append((calibration[7] << 8) | calibration[6])
        self.digP.append((calibration[9] << 8) | calibration[8])
        self.digP.append((calibration[11]<< 8) | calibration[10])
        self.digP.append((calibration[13]<< 8) | calibration[12])
        self.digP.append((calibration[15]<< 8) | calibration[14])
        self.digP.append((calibration[17]<< 8) | calibration[16])
        self.digP.append((calibration[19]<< 8) | calibration[18])
        self.digP.append((calibration[21]<< 8) | calibration[20])
        self.digP.append((calibration[23]<< 8) | calibration[22])

        self.digH = []
        self.digH.append(calibration[24])
        self.digH.append((calibration[26]<< 8) | calibration[25])
        self.digH.append(calibration[27])
        self.digH.append((calibration[28]<< 4) | (0x0F & calibration[29]))
        self.digH.append((calibration[30]<< 4) | ((calibration[29] >> 4) & 0x0F))
        self.digH.append(calibration[31])

        for i in [1,2]:
            if self.digT[i] & 0x8000:
                self.digT[i] = (-self.digT[i] ^ 0xFFFF) + 1

        for i in [1,2,3,4,5,6,7,8]:
            if self.digP[i] & 0x8000:
                self.digP[i] = (-self.digP[i] ^ 0xFFFF) + 1

        for i in [1]:
            if self.digH[i] & 0x8000:
                self.digH[i] = (-self.digH[i] ^ 0xFFFF) + 1
        for i in [3,4]:
            if self.digH[i] & 0x0800:
                self.digH[i] = (-self.digH[i] ^ 0x0FFF) + 1
        for i in [5]:
            if self.digH[i] & 0x0080:
                self.digH[i] = (-self.digH[i] ^ 0x00FF) + 1

    def _get_chip_id(self):
        self.chip_id = self.bus.read_byte_data(self.address, self.ADDRESS_CHIPID)
        
    def _upload_settings_hum(self):
        self.bus.write_byte_data(self.address, self.ADDRESS_CONTROL_HUM, self._make_settings_hum())

    def _upload_settings_measurement(self):
        self.bus.write_byte_data(self.address, self.ADDRESS_CONTROL, self._make_settings_measurement())

    def _upload_settings_config(self):
        self.bus.write_byte_data(self.address, self.ADDRESS_CONFIG, self._make_settings_config())

    def _set_forced_mode(self):
        self.mode = self.MODE_FORCED
        self._upload_settings_measurement()

    def _set_sleep_mode(self):
        self.mode = self.MODE_SLEEP
        self._upload_settings_measurement()

    def _set_normal_mode(self):
        self.mode = self.MODE_NORMAL
        self._upload_settings_measurement()

    def _make_settings_hum(self):
        return self.h_os & 0x07

    def _make_settings_measurement(self):
        return ((self.t_os & 0x07) << 5) | ((self.p_os & 0x07) << 2) | self.mode

    def _make_settings_config(self):
        return ((self.standby & 0x07) << 5) | ((self.iir_filter & 0x07) << 2) | 0x00

    def _read_raw_data(self):
        if self.forced_mode:
            self._set_forced_mode()
            t_measure_max = 1.25 + (2.3 * self.t_os) + (2.3 * self.p_os + 0.575) + (2.3 * self.h_os + 0.575)
            time.sleep(t_measure_max/1000.0)
        
        data = self.bus.read_i2c_block_data(self.address, self.ADDRESS_DATA, self.DATA_LENGTH)

        self.pressure_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        self.temperature_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        self.humidity_raw = (data[6] << 8) | data[7]

        if self.forced_mode:
            self.mode = self.MODE_SLEEP


    def _calculate_parameters(self):
        self.log_message("Compensating temperature", logging.INFO)
        self.temperature_factor = ((self.temperature_raw / 16384.0 - self.digT[0] / 1024.0) * self.digT[1] +
                                  (self.temperature_raw / 131072.0 - self.digT[0] / 8192.0) ** 2 * self.digT[2])
        self.temperature_celsius = self.temperature_factor / 5120.0

        self.log_message("Compensating pressure", logging.INFO)
        var1 = self.temperature_factor / 2.0 - 64000.0
        var2 = var1 ** 2 * (self.digP[5]) / 32768.0
        var2 = var2 + var1 * (self.digP[4]) * 2.0
        var2 = (var2 / 4.0)+(self.digP[3] * 65536.0)
        var1 = (self.digP[2] * var1 * var1 / 524288.0 + self.digP[1] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0)*self.digP[0]
        if var1 == 0.0:
            self.pressure_pascals = 0
        else:
            p = 1048576.0 - self.pressure_raw
            p = (p - (var2 / 4096.0)) * 6250.0 / var1
            var1 = self.digP[8] * p ** 2 / 2147483648.0
            var2 = p * self.digP[7] / 32768.0
            self.pressure_pascals = p + (var1 + var2 + self.digP[6]) / 16.0
        self.pressure_mm_hg = self.pressure_pascals / 133.322

        self.log_message("Compensating humidity", logging.INFO)
        var_H = self.temperature_factor - 76800.0
        var_H = (self.humidity_raw - (self.digH[3] * 64.0 + self.digH[4] / 16384.0 * var_H)) * (self.digH[1] / 65536.0 * (1.0 + self.digH[5] / 67108864.0 * var_H * (1.0 + self.digH[2] / 67108864.0 * var_H)))
        var_H = var_H * (1.0 - self.digH[0] * var_H / 524288.0)
        if var_H > 100.0:
            var_H = 100.0
        elif var_H < 0.0:
            var_H = 0.0
        self.humidity_percent = var_H
        dewpoint_gamma = 17.27 * self.temperature_celsius / (237.7 + self.temperature_celsius) + log(self.humidity_percent)
        self.dewpoint_celsius = 17.27 * dewpoint_gamma / (237.7 - dewpoint_gamma)


# Overriding defaults

    def get_current_reading(self, src_id=None):
        self.log_message("Reading values via I2C bus",logging.INFO)
        self._read_raw_data()
        self._calculate_parameters()     
        reading = []
        reading.append({"name": "Chip_ID",
                   "measured_parameter": "id",
                   "units": "",
                   "type": "Text",
                   "reading": self.chip_id})
        reading.append({"name": "Temperature",
                   "measured_parameter": "temperature",
                   "units": "°C",
                   "type": "Numeric",
                   "reading": self.temperature_celsius})
        reading.append({"name": "Pressure",
                   "measured_parameter": "pressure",
                   "units": "mm Hg",
                   "type": "Numeric",
                   "reading": self.pressure_mm_hg})
        reading.append({"name": "Humidity",
                   "measured_parameter": "humidity",
                   "units": "%",
                   "type": "Numeric",
                   "reading": self.humidity_percent})
        reading.append({"name": "Dewpoint",
                   "measured_parameter": "temperature",
                   "units": "°C",
                   "type": "Numeric",
                   "reading": self.dewpoint_celsius})
        return reading