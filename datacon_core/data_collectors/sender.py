from .proto import Collector
import json
import requests

class JSONSender(Collector):

    def __init__(self, name, description, address="127.0.0.1", port="80"):
        self._address = address
        self._port = port
        super().__init__(name, description)

    def upload_data(self, data):
        data = str(data, 'utf-8')
        # TODO: send to address