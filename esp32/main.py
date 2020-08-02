from bme280 import BME280
from bh1750 import BH1750
from machine import I2C, Pin
from time import sleep, sleep_ms
import gc

i2c = I2C(scl=Pin(22), sda=Pin(21))
sleep_ms(500)
bme = BME280("Main", i2c)
bh = BH1750("Light", i2c)
sleep(1)
bh.setup(sensitivity=150, mode=bh.MODE_CONTINUOUS)
print(bme.chip_id)
while True:
    bh.request_data()
    sleep(1)
    bme.read_data()
    bh.read_data()
    print("Temp is " + str(bme.temperature_celsius))
    print("Humidity is " + str(bme.humidity_percent))
    print("Pressure is " + str(bme.pressure_mm_hg))
    print("Dewpoint is " + str(bme.dewpoint_celsius))
    print("Light intensity is " + str(bh.light_intensity_lx))
    print("Free mem is " + str(gc.mem_free()))
    print("------")
