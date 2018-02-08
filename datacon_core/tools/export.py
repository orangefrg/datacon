import json, sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone


filename = sys.argv[1]
parameters = {}
import_json = []
i = 0
with open(filename) as f:
    for l in f.readlines():
        js = json.loads(l)
        i += 1
        print("Line {}...".format(i))
        time = datetime.strptime(js["time"], "%Y-%m-%dT%H:%M:%S.%f")
        for prov in js["data"]:
            duration = datetime.strptime(prov["end_time"], "%Y-%m-%dT%H:%M:%S.%f") - datetime.strptime(prov["start_time"], "%Y-%m-%dT%H:%M:%S.%f")
            duration = duration.total_seconds()
            prov["reading"].append({"name": "Parameter measurement",
                                    "measured_parameter": "duration",
                                    "units": "s",
                                    "reading": duration})
            for r in prov["reading"]:
                param_name = "{}.{}.{}".format(prov["name"], r["name"], r["measured_parameter"])
                if param_name not in parameters:
                    parameters[param_name] = {"units": r["units"]}
                    parameters[param_name]["readings"] = []
                if "reading" in r:
                    parameters[param_name]["readings"].append((js["time"], r["reading"]))

    