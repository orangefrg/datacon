from .proto import Collector
import json
import requests

class JSONSender(Collector):

    def __init__(self, name, description, routing_keys=[], amqp=True, address="http://127.0.0.1"):
        self._address = address
        super().__init__(name, description, routing_keys, amqp)

    def upload_data(self, data):
        data = {"message": str(data, 'utf-8')}
        try:
            r = requests.post(self._address, verify=False, data=data)
            self.log_message(r.text)
            return r.status_code == requests.codes.ok
        except requests.ConnectionError:
            self.log_message("Connection error")
        except requests.Timeout:
            self.log_message("Timeout exceeded")
        except requests.RequestException:
            self.log_message("Request error")
        except:
            self.log_message("Unspecified error")
        return False
