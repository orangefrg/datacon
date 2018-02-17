import pika, json, threading

DEFAULT_EXCHANGE = "MainData"

# Thread prototype

class CollectorThread(threading.Thread):
   def __init__(self, collector):
      threading.Thread.__init__(self)
      self.collector = collector
   def run(self):
      self.collector._make_connection()

# Collector is a final recepient of data
# Collector has ability to receive messages via AMQP
# If no AMQP is needed, one may simply call upload_data


class Collector:

    def log_message(self, message):
        print("{}: {}".format(self._name, message))

    # Should return true on successful upload
    # Otherwise, return false
    def upload_data(self, data):
        raise NotImplementedError

    def get_name(self):
        return self._name
    
    def get_description(self):
        return self._description

    # Various pika-related callbacks
    def _receive_callback(self, ch, method, properties, body):
        if self.upload_data(body):
            ch.basic_ack(delivery_tag = method.delivery_tag)

    def _on_declare_queue(self, queue):
        self.log_message("QUEUE OK")    
        self._channel.basic_qos(prefetch_count=1)
        for k in self._routing_keys:
                self.log_message("BINDING {}...".format(k))
                self._channel.queue_bind(None, "{}.collectq".format(self._name), DEFAULT_EXCHANGE, "{}.collect".format(k), nowait=True)
                self._channel.queue_bind(None, "{}.collectq".format(self._name), DEFAULT_EXCHANGE, "{}.all".format(k), nowait=True)
                self.log_message("BIND {} OK".format(k))
        self._consumer_tag = self._channel.basic_consume(self._receive_callback)

    def _on_open_channel(self, channel):
        self.log_message("CHANNEL OK")
        self._channel = channel
        self.log_message("QUEUE...")    
        self._channel.queue_declare(self._on_declare_queue, queue="{}.collectq".format(self._name), durable=True)

    def _on_open_connection(self, connection):
        self.log_message("CONNECTION OK")
        self.log_message("CHANNEL...")
        self._connection.channel(self._on_open_channel)
    
    def _on_error_connection(self, connection, error=""):
        self.log_message(error)

    def _make_connection(self):
        self.log_message("CONNECT...")
        self._connection = pika.SelectConnection(on_open_callback=self._on_open_connection,
                              on_open_error_callback=self._on_error_connection)
        self._connection.ioloop.start()

    # If no routing keys are provided, EVERY message ending with ".collect" will be accepted
    # Queues are declared automatically, as well as bindings
    # Be sure to remove abandoned ones
    def __init__(self, name, description, routing_keys=[], amqp=True):
        self._name = name
        self.log_message("INIT...")
        self._description = description
        if amqp:
            self._consumer_tag = ""
            self._routing_keys = ["*"] if routing_keys is None or len(routing_keys) == 0 else routing_keys
            self._ct = CollectorThread(self)
            self._ct.start()

    def _process_message(self, message):
        return json.loads(message)
