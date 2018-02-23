import time
import datetime
import json
import sys
from data_providers.ds18b20 import Ds18b20
from data_providers.opi_selfdiag import OrangePiSelfDiag
from data_providers.htu21d import HTU21D
from data_providers.heartbeat import Heartbeat
from data_collectors.simple import SimplePrinter, SimpleFileWrite
from data_collectors.sender import JSONSender
from rmq_config import initial_config
from apscheduler.schedulers.background import BackgroundScheduler
import shared_config
import logging

logging.basicConfig(filename='datacon_main.log', level=logging.WARNING)

initial_config()
sch = BackgroundScheduler()
sch.start()
# filename = sys.argv[1]

ALIASES = {"28-0000043a174f": "Outside",
           "28-0000041b3610": "Inside"}

DALLAS = Ds18b20("DS1", "Local dallas sensors", sch, publish_routing_key="all.collect", sensor_aliases=ALIASES)
ORANGE = OrangePiSelfDiag("OPi1", "Orange Pi one and only", sch, publish_routing_key="all.collect")
HTU = HTU21D("GY-21", "Temperature and humidity measurement", sch, publish_routing_key="all.collect")
HB = Heartbeat("Heartbeat", "Data provider for test purposes", sch, publish_routing_key="all.collect")

DALLAS.set_polling({"cron": {"minute": "0-50/10"}})
ORANGE.set_polling({"cron": {"minute": "1-51/10"}})
HTU.set_polling({"cron": {"minute": "0-50/10"}})
HB.set_polling({"cron": {"minute": "2-52/10"}})

DALLAS.activate_polling()
ORANGE.activate_polling()
HTU.activate_polling()
HB.activate_polling()

# PRINTER = SimplePrinter("printer", "Default console printer", ["all", "printer"])
SENDER = JSONSender("json-sender", "Simple JSON HTTP(S) sender", ["all", "sender"], address=shared_config.URL_TO_SEND)
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
                time.sleep(5)
except KeyboardInterrupt:
        print("End")
        
        
