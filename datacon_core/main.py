import time
import datetime
import json
import sys
from data_providers.ds18b20 import Ds18b20
from data_providers.opi_selfdiag import OrangePiSelfDiag
from data_providers.htu21d import HTU21D
from data_providers.heartbeat import Heartbeat
from data_collectors.simple import SimplePrinter, SimpleFileWrite
from rmq_config import initial_config
from apscheduler.schedulers.background import BackgroundScheduler

initial_config()
sch = BackgroundScheduler()
# filename = sys.argv[1]

ALIASES = {"28-0000043a174f": "Outside",
           "28-0000041b3610": "Inside"}

# DALLAS = Ds18b20("DS1", "Local dallas sensors", sensor_aliases=ALIASES)
# ORANGE = OrangePiSelfDiag("OPi1", "Orange Pi one and only")
# HTU = HTU21D("GY-21", "Temperature and humidity measurement")
HB = Heartbeat("Heartbeat", "Data provider for test purposes", sch, publish_routing_key="printer.collect")
HB.set_polling({"delay": 5})
HB.activate_polling()

PRINTER = SimplePrinter("printer", "Default console printer", ["all", "printer"])
# WRITER = SimpleFileWrite("writer", "Deafult file writer", ["all", "writer"], False, "test_with_rabbit")

# DALLAS.set_polling({"cron": {"minute": "0-50/10"}}, [WRITER, PRINTER])
# ORANGE.set_polling({"cron": {"minute": "0-55/5"}}, [WRITER, PRINTER])
# HTU.set_polling({"cron": {"minute": "0-50/10"}}, [WRITER, PRINTER])
# HTU.set_polling({"delay": 10}, [])
# DALLAS.activate_polling()
# ORANGE.activate_polling()
# HTU.activate_polling()


try:
        while True:
                time.sleep(2)
except KeyboardInterrupt:
        print("End")
        
        
