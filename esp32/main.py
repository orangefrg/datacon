from bme280 import BME280
from bh1750 import BH1750
from machine import I2C, Pin, RTC
from network import WLAN
from time import sleep, sleep_ms
from micropython import const
from upload import HTTPUploader
import gc
import shared_config
import ntptime
import ujson

NTP_CYCLE_COUNT = const(40) # sync to NTP every N cycles
MAX_CONNECT_COUNT = const(5)
CONNECTION_TIMEOUT = const(10)

def check_connect():
    if wlan.isconnected():
        return True
    wlan.active(True)
    networks = wlan.scan()
    for n in networks:
        if n[0] == shared_config.wifi_ssid.encode():
            wlan.connect(shared_config.wifi_ssid, shared_config.wifi_pass)
            connection_attempt = 1
            while(not wlan.isconnected()):
                sleep(CONNECTION_TIMEOUT)
                connection_attempt += 1
                if connection_attempt >= MAX_CONNECT_COUNT:
                    return False                
            print("Connected!")
            return True
    return False

print("---Initializing---")
print("---Wi-Fi---")
wlan = WLAN()
connected = check_connect()

print("---Time---")
rtc = RTC()
if connected:
    ntptime.settime()

while rtc.datetime()[0] <= 2007:
    print("RTC inaccurate, sleeping for 10 min till next NTP try")
    sleep(15) #15 secs for debugging
    if check_connect():
        ntptime.settime()

print("---I2C Bus---")
i2c = I2C(scl=Pin(22), sda=Pin(21))
sleep_ms(500)

print("---I2C Sensors---")
bme = BME280("BME.Inside", rtc, i2c)
bh = BH1750("Luminosity.Inside", rtc, i2c)

print("---Uploader---")
uploader = HTTPUploader(shared_config.upload_url)

sleep(1)
bh.setup(sensitivity=150, mode=bh.MODE_CONTINUOUS)
print(bme.chip_id)

cycle_counter = 0

while True:
    if not check_connect():
        "WARNING: network offline"
    bh.request_data()
    sleep(1)
    bme_msg = bme.get_readings()
    bh_msg = bh.get_readings()
    print("Free mem is " + str(gc.mem_free()))
    for msg in bme.get_splitted_message():
        uploader.add_message(msg)
        print("---\n{}\n---".format(msg))
    for msg in bh.get_splitted_message():
        uploader.add_message(msg)
        print("---\n{}\n---".format(msg))
    if check_connect():
        uploader.upload()
        print("Upload OK")
        if cycle_counter >= NTP_CYCLE_COUNT:
            ntptime.settime()
            cycle_counter = 0
            print("NTP Sync OK")
    if cycle_counter < NTP_CYCLE_COUNT:
        cycle_counter += 1
    else:
        print("Skipping NTP sync due to lack of connection")
