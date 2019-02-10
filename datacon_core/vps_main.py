#!/usr/bin/python3

import time
import datetime
import json
import sys
from data_providers.vps_selfdiag import VPSSelfDiag
from data_providers.nix_network import ConnectionMon
from data_collectors.sender import JSONSender
from rmq_config import initial_config
from apscheduler.schedulers.background import BackgroundScheduler
import shared_config
import logging

logging.basicConfig(filename='datacon_main.log', level=logging.WARNING)

# initial_config()
sch = BackgroundScheduler()
sch.start()

VPS = VPSSelfDiag("VPS-Z", "VPS self-diag", sch, broker="redis", if_name="ens3",
                  if_alias = "IP-1", free_space_path="/")
NET_1 = ConnectionMon("VPS-Z", "VPS network 1", sch,
                      broker="redis", connection_filter={
                                        "alias_if": "IP-1",
                                        "alias_conn": shared_config.ALIAS_1,
                                        "iface": shared_config.NET_IF,
                                        "port": shared_config.NET_PORT_1
                                })
NET_2 = ConnectionMon("VPS-Z", "VPS network 2", sch,
                      broker="redis", connection_filter={
                                        "alias_if": "IP-1",
                                        "alias_conn": shared_config.ALIAS_2,
                                        "iface": shared_config.NET_IF,
                                        "port": shared_config.NET_PORT_2
                                })
# NET_3 = ConnectionMon("VPS-Z", "VPS network 3", sch,
#                      broker="redis", connection_filter={
#                                        "alias_if": "IP-1",
#                                        "alias_conn": shared_config.ALIAS_3,
#                                        "iface": shared_config.NET_IF,
#                                        "port": shared_config.NET_PORT_3
#                                })
VPS.set_polling({"cron": {"minute": "0-50/10"}})
NET_1.set_polling({"cron": {"minute": "2-52/10"}})
NET_2.set_polling({"cron": {"minute": "3-53/10"}})
# NET_3.set_polling({"cron": {"minute": "4-54/10"}})
VPS.activate_polling()
NET_1.activate_polling()
NET_2.activate_polling()
# NET_3.activate_polling()

senders = []
for i in range(1):
        senders.append(JSONSender("json-sender-{}".format(i), "Simple JSON HTTP(S) sender", "json-sender", ["all", "sender"], address=shared_config.URL_TO_SEND,       
                                  broker="redis"))

try:
        while True:
                time.sleep(50)
except KeyboardInterrupt:
        print("End")
        
        
