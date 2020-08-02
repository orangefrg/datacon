# 2020-08-02T14:21:39Z

def isoformat(dt):
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:06d}".format(dt[0], dt[1], dt[2], 
                                                                dt[4], dt[5], dt[6], dt[7])

class DataProvider:

    def __init__(self, name, rtc):
        self.name = name
        self.rtc = rtc
        self.message = {}

    def _start_message(self):
        self.message["name"] = self.name
        self.message["start_time"] = isoformat(self.rtc.datetime())

    def _finalize_message(self, readings):
        self.message["reading"] = readings
        self.message["end_time"] = isoformat(self.rtc.datetime())

    def get_splitted_message(self):
        return [{
            "name": self.message["name"],
            "start_time": self.message["start_time"],
            "end_time": self.message["end_time"],
            "reading": [r]
        } for r in self.message["reading"]]