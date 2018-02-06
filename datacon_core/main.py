import time
import datetime
import json
from data_providers.ds18b20 import Ds18b20
from data_providers.opi_selfdiag import OrangePiSelfDiag

ALIASES = {"28-0000043a174f": "Outside",
           "28-0000041b3610": "Inside"}

DALLAS = Ds18b20("DS1", "Local dallas sensors", ALIASES)
ORANGE = OrangePiSelfDiag("OPi1", "Orange Pi one and only")


while True:
    with open("results", "a+") as f:
        cur = DALLAS.get_current_reading()
        orn = ORANGE.get_current_reading()
        data = {"time": datetime.datetime.utcnow().isoformat(),
                "data": [cur, orn]}
        f.write(json.dumps(data, sort_keys=True))
        f.write("\n")
        print("------------")
        print(json.dumps(data, sort_keys=True, indent=2))
        time.sleep(30)
