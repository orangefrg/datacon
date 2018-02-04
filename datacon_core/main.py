import time
import json
from data_providers.ds18b20 import Ds18b20

ALIASES = {"28-0000043a174f": "Outside"}

DALLAS = Ds18b20("DS1", "Local dallas sensors", ALIASES)

while True:
    cur = DALLAS.get_current_reading()
    print(json.dumps(cur, sort_keys=True, indent=2))
    time.sleep(20)
