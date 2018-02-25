from .proto import Collector
import json
import requests
import logging
import traceback
import sys
import threading

class JSONSender(Collector):

    def __init__(self, name, description, queue_name_prefix=None, routing_keys=[], amqp=True, loglevel=logging.DEBUG, address="http://127.0.0.1"):
        self._address = address
        self._threads = []
        super().__init__(name, description, queue_name_prefix, routing_keys, amqp, loglevel)     

    def upload_data(self, data):
        self.log_message("Trying to upload: {}".format(data), logging.DEBUG) 
        data = {"message": str(data, 'utf-8')}
        try:
            self.log_message("POST request to {}".format(self._address), logging.DEBUG) 
            r = requests.post(self._address, verify=False, data=data)
            self.log_message(r.text)
            resp = r.status_code
            self.log_message("Response is {}".format(resp), logging.DEBUG)
            if resp == requests.codes.ok:
                return True
            else:
                self.log_message("Abnormal response - {}".format(resp), logging.ERROR)
        except requests.ConnectionError:
            self.log_message("Connection error", logging.ERROR)
        except requests.Timeout:
            self.log_message("Timeout exceeded", logging.ERROR)
        except requests.RequestException:
            self.log_message("Request error", logging.ERROR)
        except:
            self.log_message("Unspecified error: {}".format(sys.exc_info()[0]), logging.ERROR)
        return False
