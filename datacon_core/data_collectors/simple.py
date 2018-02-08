from .proto import Collector
import json


class SimplePrinter(Collector):

    def __init__(self):
        self._active = False

    def upload_data(self, data, forward=None):
        if self._active:
            print(json.dumps(data, sort_keys=True, indent=2))
        if forward is not None and len(forward)>0:
            forward[0].upload_data(data, forward[1:])
    
    def set_online(self):
        self._active = True
    def set_offline(self):
        self._active = False


class SimpleFileWrite(Collector):

    def __init__(self, filename=None):
        self._active = False
        self._filename = filename if filename is not None else "simple_file_write"

    def upload_data(self, data, forward=None):
        if self._active:
            with open(self._filename, "a+") as f:
                f.write(json.dumps(data, sort_keys=True) + "\n")
        if forward is not None and len(forward)>0:
            forward[0].upload_data(data, forward[1:])
    
    def set_online(self):
        self._active = True
    def set_offline(self):
        self._active = False