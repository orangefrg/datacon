

class Collector:

    def upload_data(self, data, forward=None):
        raise NotImplementedError
    
    def set_online(self):
        raise NotImplementedError
    def set_offline(self):
        raise NotImplementedError