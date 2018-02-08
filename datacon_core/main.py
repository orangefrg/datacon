import time
import datetime
import json
from data_providers.ds18b20 import Ds18b20
from data_providers.opi_selfdiag import OrangePiSelfDiag
from data_collectors.simple import SimplePrinter, SimpleFileWrite

ALIASES = {"28-0000043a174f": "Outside",
           "28-0000041b3610": "Inside"}

DALLAS = Ds18b20("DS1", "Local dallas sensors", ALIASES)
ORANGE = OrangePiSelfDiag("OPi1", "Orange Pi one and only")
PRINTER = SimplePrinter()
WRITER_T = SimpleFileWrite("res_temp-2018-02-08")
WRITER_D = SimpleFileWrite("res_diag-2018-02-08")

PRINTER.set_online()
WRITER_T.set_online()
WRITER_D.set_online()

DALLAS.set_polling({"cron": {"minute": "0-45/15"}}, [WRITER_T, PRINTER])
ORANGE.set_polling({"cron": {"minute": "0-55/5"}}, [WRITER_D, PRINTER])
# DALLAS.set_polling({"delay": 15}, [WRITER, PRINTER])
# ORANGE.set_polling({"delay": 15}, [WRITER, PRINTER])
DALLAS.activate_polling()
ORANGE.activate_polling()

try:
        while True:
                time.sleep(2)
except KeyboardInterrupt:
        print("End")
        
        
