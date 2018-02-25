import time
import datetime
import json
import sys
from data_providers.vps_selfdiag import VPSSelfDiag
from data_collectors.sender import JSONSender
from rmq_config import initial_config
from apscheduler.schedulers.background import BackgroundScheduler
import shared_config
import logging

logging.basicConfig(filename='datacon_main.log', level=logging.WARNING)

initial_config()
sch = BackgroundScheduler()
sch.start()

VPS = VPSSelfDiag("VPS-Z", "Zomro VPS self-diag", sch, publish_routing_key="all.collect")
VPS.set_polling({"cron": {"minute": "0-50/10"}})
VPS.activate_polling()

senders = []
for i in range(3):
        senders.append(JSONSender("json-sender-{}".format(i), "Simple JSON HTTP(S) sender", "json-sender", ["all", "sender"], address=shared_config.URL_TO_SEND))

try:
        while True:
                time.sleep(5)
except KeyboardInterrupt:
        print("End")
        
        
