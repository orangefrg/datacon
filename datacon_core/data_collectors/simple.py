from .proto import Collector
import json


class SimplePrinter(Collector):

    def __init__(self, name, description, routing_keys=[], amqp=True, process_as_json=True):
        self._process_as_json = process_as_json
        super().__init__(name, description, routing_keys, amqp)

    def upload_data(self, data):
        data = str(data, 'utf-8')
        if self._process_as_json:
            print(json.dumps(self._process_message(data), sort_keys=True, indent=2))
        else:
            print(data)
        return True


class SimpleFileWrite(Collector):

    def __init__(self, name, description, routing_keys=[], amqp=True, process_as_json=True, filename=None):
        self._filename = filename if filename is not None else "simple_file_write"
        self._process_as_json = process_as_json
        super().__init__(name, description, routing_keys, amqp)

    def upload_data(self, data):
        data = str(data, 'utf-8')
        with open(self._filename, "a+") as f:
            if self._process_as_json:
                json_data = json.loads(data)
                f.write(json.dumps(self._process_message(data), sort_keys=True) + "\n")
            else:
                f.write(data + "\n")
        return True
