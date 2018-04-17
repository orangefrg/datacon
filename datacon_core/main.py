#!/usr/bin/python3

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

# shared_config.py should contain following:
#
# URL_TO_SEND = "Server URL here"
# DS = "Datasource UID here"
# CERT_FILE = "SSL .crt file from server here"
#

ALIASES = {"28-0000043a174f": "Outside",
           "28-0000041b3610": "Inside"}

DALLAS = Ds18b20("DS1", "Local dallas sensors", sch, publish_routing_key="all.collect", sensor_aliases=ALIASES)
ORANGE = OrangePiSelfDiag("OPi1", "Orange Pi one and only", sch, publish_routing_key="all.collect")
HTU = HTU21D("GY-21", "Temperature and humidity measurement", sch, publish_routing_key="all.collect")

DALLAS.set_polling({"cron": {"minute": "0-50/10"}})
ORANGE.set_polling({"cron": {"minute": "0-50/10"}})
HTU.set_polling({"cron": {"minute": "0-50/10"}})

DALLAS.activate_polling()
ORANGE.activate_polling()
HTU.activate_polling()

# PRINTER = SimplePrinter("printer", "Default console printer", ["all", "printer"])
senders = []
for i in range(10):
        senders.append(JSONSender("json-sender-{}".format(i), "Simple JSON HTTP(S) sender", "json-sender", ["all", "sender"],
                                  address=shared_config.URL_TO_SEND, cert=shared_config.CERT_FILE))
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
        
        
