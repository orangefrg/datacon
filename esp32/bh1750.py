from utime import time
from provider_proto import DataProvider

class BH1750(DataProvider):

    DEFAULT_ADDRESS_LOW = 0x23 # Addr pin is left floating or pulled down
    DEFAULT_ADDRESS_HIGH = 0x5C # Addr pin is pulled up

    SENSITIVITY_HIGH_CMD = 0x40
    SENSITIVITY_LOW_CMD = 0x60
    POWER_OFF = 0x00
    POWER_ON = 0x01
    RESET = 0x07

    RES_05 = 0x01
    RES_1 = 0x00
    RES_4 = 0x03

    TIME_HIRES = 0.16
    TIME_LORES = 0.02
    
    MODE_CONTINUOUS = 0x10
    MODE_ONETIME = 0x20

    DEFAULT_LIGHT_SENSITIVITY = 69 # 31 to 254

    def __init__(self, name, rtc, i2c_bus, address=DEFAULT_ADDRESS_LOW):
        self.bus = i2c_bus
        self.address = address
        self.data_buffer = bytearray(2)
        self.light_intensity_lx = None
        super().__init__(name, rtc)

    def _write_mode_and_res(self):
        self.bus.writeto(self.address, bytearray([self.mode + self.resolution]))

    def _write_sensitivity(self):
        if self.sensitivity < 31 or self.sensitivity > 254:
            return
        self.bus.writeto(self.address, bytearray([self.sensitivity >> 5 | self.SENSITIVITY_HIGH_CMD]))
        self.bus.writeto(self.address, bytearray([self.sensitivity & 0xF | self.SENSITIVITY_LOW_CMD]))

    def setup(self, is_continuous=False, sensitivity=DEFAULT_LIGHT_SENSITIVITY,
            mode=MODE_CONTINUOUS, resolution=RES_1):
        self.mode = mode
        self.is_powered = False
        self.sensitivity = sensitivity
        self.resolution = resolution

    def power_on(self):
        self.bus.writeto(self.address, bytearray([self.POWER_ON]))
        self._write_sensitivity()
        self.is_powered = True

    def power_off(self):
        self.bus.writeto(self.address, bytearray([self.POWER_OFF]))
        self.is_powered = False

    def _perform_correction(self):
        if self.light_intensity_lx is not None:
            if self.light_intensity_lx >= 65000 and self.sensitivity > 31:
                self.sensitivity -= 20
                if self.sensitivity < 31:
                    self.sensitivity = 31
                print("BH1750 decreases sensitivity to {}".format(self.sensitivity))
            elif self.light_intensity_lx <= 5 and self.sensitivity < 254:
                self.sensitivity += 20
                if self.sensitivity > 254:
                    self.sensitivity = 254
                print("BH1750 increases sensitivity to {}".format(self.sensitivity))
        self._write_sensitivity()

    # Time (in seconds) needed to measure light is returned
    # if device is not powered, None is returned
    def request_data(self, allow_corrections=True):
        self._start_message()
        if not self.is_powered:
            self.power_on()
        if allow_corrections:
            self._perform_correction()
        self._write_mode_and_res()
        if self.mode == self.MODE_ONETIME:
            self.is_powered = False
        if self.resolution == self.RES_4:
            return self.TIME_LORES * (self.sensitivity/self.DEFAULT_LIGHT_SENSITIVITY)
        else:
            return self.TIME_HIRES * (self.sensitivity/self.DEFAULT_LIGHT_SENSITIVITY)
    
    def _read_data(self):
        self.bus.readfrom_into(self.address, self.data_buffer)
        raw_lx = (self.data_buffer[0] << 8 | self.data_buffer[1]) / 1.2
        if self.resolution == self.RES_05:
            raw_lx *= 2
        self.light_intensity_lx = raw_lx * (self.DEFAULT_LIGHT_SENSITIVITY / self.sensitivity)

    def get_readings(self):
        self._read_data()  
        readings = []
        readings.append({"name": "Light",
                   "measured_parameter": "intensity",
                   "units": "lx",
                   "type": "Numeric",
                   "reading": self.light_intensity_lx})
        readings.append({"name": "Light",
                   "measured_parameter": "sensitivity",
                   "units": "",
                   "type": "Numeric",
                   "reading": self.sensitivity})
        self._finalize_message(readings)
        return self.message