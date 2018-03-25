import sched, time
from pika import BlockingConnection
import json
import logging
from datetime import datetime
import sys

DEFAULT_EXCHANGE = "MainData"

# Data provider
# Main abstract class for implementing data collection entities

class Provider:


    def log_message(self, message, level=40):
        if level > self._loglevel:
            message_out = "{:%Y-%m-%d %H:%M:%S.%f}: {} [{}]: {}".format(datetime.utcnow(),
                                                                    self._name,
                                                                    self.LOG_LEVELS[level][1],
                                                                    message)
            print(message_out)
            self.LOG_LEVELS[level][0](message_out)


    def _revoke_channel(self):
        self.log_message("Connecting to AMQP broker...", logging.DEBUG)
        try:
            self._connection = BlockingConnection()
            self._channel = self._connection.channel()
        except:
            self.log_message("Connection failed: {}".format(sys.exc_info()[0]), logging.ERROR)
        self.log_message("Connection OK", logging.DEBUG)
            
    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None, loglevel=logging.DEBUG):
        self._sched = scheduler
        self._name = name
        self._description = description
        self._loglevel = loglevel
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(loglevel)
        self.LOG_LEVELS = {50: (self._logger.critical, "Critical"),
                           40: (self._logger.error, "Error"),
                           30: (self._logger.warning, "Warning"),
                           20: (self._logger.info, "Info"),
                           10: (self._logger.debug, "Debug")}
        self.log_message("{} is being initialized".format(self._name), logging.INFO)
        self._invalid_config = not amqp and (pass_to is None or len(pass_to) == 0)

        if amqp:
            self.log_message("Setting up AMQP", logging.INFO)
            self._pass_to = None
            self._publish_routing_key = publish_routing_key
            try:
                self._connection = BlockingConnection()
                self._channel = self._connection.channel()
            except:
                self.log_message("Connection failed: {}".format(sys.exc_info()[0]), logging.ERROR)
            if command_routing_keys is not None and len(command_routing_keys) > 0:
                try:
                    self.log_message("Subscribing to queue", logging.INFO)
                    self._channel.queue_declare(queue="{}.provideq".format(self._name), durable=True)
                    for k in command_routing_keys:
                        self._channel.queue_bind("{}.provideq".format(self._name), DEFAULT_EXCHANGE, "{}.provide".format(k))
                except:
                    self.log_message("Queue declaring failed: {}".format(sys.exc_info()[0]), logging.ERROR)
            self._connection.close()
            self.log_message("AMQP connection OK", logging.INFO)
        else:
            self.log_message("No AMQP - passing mode enabled", logging.WARNING)
            self._pass_to = pass_to

    def get_name(self):
        return self._name
    def get_description(self):
        return self._description

    # Make message prototype with measurement start time, module name and readings list
    def _start_message(self):
        message = {}
        message["name"] = self._name
        message["start_time"] = datetime.utcnow().isoformat()
        message["reading"] = []
        return message

    # Add measurement finish time to message
    def _finalize_message(self, message):
        message["end_time"] = datetime.utcnow().isoformat()
        return message

    # Current reading should be a dictionary:
    # name - provider name
    # start_time, end_time - UTC times of start and end of measurement
    # reading - list of following dicts:
    # - name - sensor name
    # - measured_parameter - measured parameter type (e.g. temperature)
    # - type - current parameter type (Numeric, Discrete or Text)
    # - reading - current sensor reading
    # - units - reading units (optional)
    # - error - error name (optional)
    def get_current_reading(self, src_id=None):
        raise NotImplementedError

    def _poll_current_reading(self):
        self.log_message("Time to get data and send it", logging.DEBUG)
        current_rdg = self._start_message()
        current_rdg["reading"].extend(self.get_current_reading())
        current_data = json.dumps(self._finalize_message(current_rdg))
        if not self._invalid_config and self._pass_to is None:
            self.log_message("Revoking channel", logging.DEBUG)
            self._revoke_channel()
            self._channel.publish(DEFAULT_EXCHANGE, self._publish_routing_key, current_data)
            self._connection.close()
        else:
            self.log_message("Sending in simple way", logging.DEBUG)
            for collector in self._pass_to:
                collector.upload_data(current_data)

    # Activate and deactivate scheduled data retrieval
    # time_settings is a dict with following fields:
    # delay: interval in seconds (integer)
    # cron: dict of cron values -
    # year, month, day, week, day_of_week, hour, minute, second
    # if both delay and cron are passed, the delay will be used
    # collectors is a list of data collectors
    def set_polling(self, time_settings):
        self.log_message("Setting up schedule", logging.INFO)
        if "delay" in time_settings:
            self.log_message("Declaring job as delayed", logging.DEBUG)
            self._job_id = self._sched.add_job(self._poll_current_reading, "interval", seconds=time_settings["delay"]).id
            self._sched.pause_job(job_id=self._job_id)

        elif "cron" in time_settings:
            for p in ["year", "month", "day", "week", "day_of_week", "hour", "minute", "second"]:
                if p not in time_settings["cron"]:
                    time_settings["cron"][p] = None
            self.log_message("Declaring job as cron-set", logging.DEBUG)
            self._job_id = self._sched.add_job(self._poll_current_reading, "cron",
            year=time_settings["cron"]["year"], month=time_settings["cron"]["month"],
            day=time_settings["cron"]["day"], week=time_settings["cron"]["week"],
            day_of_week=time_settings["cron"]["day_of_week"], hour=time_settings["cron"]["hour"],
            minute=time_settings["cron"]["minute"], second=time_settings["cron"]["second"]).id
            self._sched.pause_job(job_id=self._job_id)
        else:
            return False
        return True

    def activate_polling(self):
        self.log_message("Resuming job", logging.INFO)
        self._sched.resume_job(job_id=self._job_id)
    def deactivate_polling(self):
        self.log_message("Pausing job", logging.INFO)
        self._sched.pause_job(job_id=self._job_id)

    def set_parameter(self, parameter_name, parameter_value):
        raise NotImplementedError
    def get_parameter(self, parameter_name):
        raise NotImplementedError