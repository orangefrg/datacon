import pika, redis, json, threading
import logging
from datetime import datetime

LOG_LEVELS = {50: (logging.critical, "Critical"),
              40: (logging.error, "Error"),
              30: (logging.warning, "Warning"),
              20: (logging.info, "Info"),
              10: (logging.debug, "Debug")}

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

    def log_message(self, message, level=40):
        if level > self._loglevel:
            message_out = "{:%Y-%m-%d %H:%M:%S.%f}: {} [{}]: {}".format(datetime.utcnow(),
                                                                    self._name,
                                                                    self.LOG_LEVELS[level][1],
                                                                    message)
            print(message_out)
            self.LOG_LEVELS[level][0](message_out)

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
        self.log_message("Message received: {}".format(body), logging.DEBUG) 
        if self.upload_data(body):
            ch.basic_ack(delivery_tag = method.delivery_tag)
        else:
            ch.basic_reject(delivery_tag = method.delivery_tag, requeue = True)

    def _on_declare_queue(self, queue):
        self.log_message("Queue OK", logging.DEBUG) 
        self._channel.basic_qos(prefetch_count=1)
        for k in self._routing_keys:
            self.log_message("Binding {}".format(k), logging.DEBUG) 
            self._channel.queue_bind(None, self._queue_name, DEFAULT_EXCHANGE, "{}.collect".format(k), nowait=True)
            self._channel.queue_bind(None, self._queue_name, DEFAULT_EXCHANGE, "{}.all".format(k), nowait=True)
            self.log_message("Binding {} OK".format(k), logging.DEBUG) 
        self.log_message("Connection and setting of AMQP OK", logging.INFO) 
        self._consumer_tag = self._channel.basic_consume(self._receive_callback)

    def _on_open_channel(self, channel):
        self.log_message("Channel OK", logging.DEBUG)
        self._channel = channel
        self.log_message("Declaring or checking queue", logging.DEBUG)
        self._channel.queue_declare(self._on_declare_queue, queue=self._queue_name, durable=True)

    def _on_open_connection(self, connection):
        self.log_message("Connection OK", logging.DEBUG)
        self.log_message("Opening channel", logging.DEBUG)
        self._connection.channel(self._on_open_channel)
    
    def _on_error_connection(self, connection, error=""):
        self.log_message("Connection error: {}".format(error), logging.ERROR)

    def _make_connection(self):
        self.log_message("Connecting to AMQP broker", logging.INFO)
        self._connection = pika.SelectConnection(on_open_callback=self._on_open_connection,
                              on_open_error_callback=self._on_error_connection)
        self.log_message("Starting main IO loop", logging.DEBUG)
        self._connection.ioloop.start()

    # Redis callbacks
    def _receive_redis_data(self, channel, data):
        if not self.upload_data(data):
            self._redis.publish(channel, data)
            self.log_message("Error sending message", logging.WARNING)

    def _receive_redis_subscribe(self, channel):
        self.log_message("Subscribed to redis channel {}".format(channel), logging.INFO)

    def _receive_redis_unsubscribe(self, channel):
        self.log_message("Unsubscribed from redis channel {}".format(channel), logging.INFO)

    def _main_redis_callback(self, message):
        if message:
            self.log_message("Message received: {}".format(message), logging.DEBUG)
            if message["type"] in ["subscribe", "psubscribe"]:
                self._receive_redis_subscribe(message["channel"])
            elif message["type"] in ["unsubscribe", "punsubscribe"]:
                self._receive_redis_unsubscribe(message["channel"])
            else:
                self._receive_redis_data(message["channel"], message["data"])

    # Broker could be: "amqp" or "redis"
    # If no routing keys are provided, EVERY message ending with ".collect" will be accepted
    # Queues are declared automatically, as well as bindings
    # Be sure to remove abandoned ones
    def __init__(self, name, description, queue_name_prefix=None, routing_keys=[], broker="amqp", redis_channels=[], loglevel=logging.DEBUG):
        self._name = name
        self._loglevel = loglevel
        self._description = description
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(loglevel)
        self.LOG_LEVELS = {50: (self._logger.critical, "Critical"),
                    40: (self._logger.error, "Error"),
                    30: (self._logger.warning, "Warning"),
                    20: (self._logger.info, "Info"),
                    10: (self._logger.debug, "Debug")}
        self._logger.info("{} is being initialized".format(self._name))
        if broker == "amqp":
            self._queue_name = "{}.collectq".format(name) if queue_name_prefix is None else "{}.collectq".format(queue_name_prefix)
            self._consumer_tag = ""
            self._routing_keys = ["*"] if routing_keys is None or len(routing_keys) == 0 else routing_keys
            self._ct = CollectorThread(self)
            self._ct.start()
        elif broker == "redis":
            self._redis = redis.StrictRedis()
            self._redis_channels = redis_channels
            self._redis_pubsub = self._redis.pubsub()
            self._redis_pubsub.subscribe(**{"all": self._main_redis_callback})
            for r in self._redis_channels:
                self._redis_pubsub.psubscribe(**{r: self._main_redis_callback})
            self._ct = self._redis_pubsub.run_in_thread(sleep_time=1)


    def _process_message(self, message):
        return json.loads(message)
