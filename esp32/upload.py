import urequests2
import ujson

class HTTPUploader:

    def __init__(self, url):
        self.url = url
        self.messages = []

    def add_message(self, message):
        self.messages.append(message)

    def upload(self):
        self.failed_messages = []
        for m in self.messages:
            print(ujson.dumps(m))
            r = urequests2.post(self.url, json={"message": m})
            print(r.status_code)
            if r.status_code != 200:
                self.failed_messages.append(m)
                print("Abnormal response")
        print("{} messages, {} failed".format(len(self.messages), len(self.failed_messages)))
        self.messages = self.failed_messages.copy()
        self.failed_messages = None
        if len(self.messages) > 20:
            print("Flushing readings due to queue overflow")
            self.messages = []