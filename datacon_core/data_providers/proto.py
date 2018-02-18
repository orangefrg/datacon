import sched, time
from pika import BlockingConnection
import json

DEFAULT_EXCHANGE = "MainData"

# Data provider
# Main abstract class for implementing data collection entities

class Provider:


    def log_message(self, message):
        print("{}: {}".format(self._name, message))


    def _revoke_channel(self):
        self._connection = BlockingConnection()
        self._channel = self._connection.channel()
            
    def __init__(self, name, description, scheduler, amqp=True, publish_routing_key="all.all",
                 command_routing_keys=[], pass_to=None):
        self._sched = scheduler
        self._name = name
        self._description = description
        self._invalid_config = not amqp and (pass_to is None or len(pass_to) == 0)

        if amqp:
            self._pass_to = None
            self._publish_routing_key = publish_routing_key
            self._connection = BlockingConnection()
            self._channel = self._connection.channel()
            if command_routing_keys is not None and len(command_routing_keys) > 0:
                self._channel.queue_declare(queue="{}.provideq".format(self._name), durable=True)
                for k in command_routing_keys:
                    self._channel.queue_bind("{}.provideq".format(self._name), DEFAULT_EXCHANGE, "{}.provide".format(k))
            self._connection.close()
        else:
            self._pass_to = pass_to

    def get_name(self):
        return self._name
    def get_description(self):
        return self._description

    # Current reading should be a dictionary:
    # name - provider name
    # start_time, end_time - UTC times of start and end of measurement
    # reading - list of following dicts:
    # - name - sensor name
    # - measured_parameter - measured parameter type (e.g. temperature)
    # - reading - current sensor reading
    # - units - reading units (optional)
    # - error - error name (optional)
    def get_current_reading(self, src_id=None):
        raise NotImplementedError

    def _poll_current_reading(self):
        self.log_message("Time is up!")
        current_data = json.dumps(self.get_current_reading())
        if not self._invalid_config and self._pass_to is None:
            self.log_message("Sending to AMQP")
            self._revoke_channel()
            self._channel.publish(DEFAULT_EXCHANGE, self._publish_routing_key, current_data)
            self._connection.close()
        else:
            self.log_message("Sending in simple way")
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
        if "delay" in time_settings:
            self.log_message("Declaring job")
            self._job_id = self._sched.add_job(self._poll_current_reading, "interval", seconds=time_settings["delay"]).id
            self.log_message("Initially pausing job")
            self._sched.pause_job(job_id=self._job_id)

        elif "cron" in time_settings:
            for p in ["year", "month", "day", "week", "day_of_week", "hour", "minute", "second"]:
                if p not in time_settings["cron"]:
                    time_settings["cron"][p] = None
            self.log_message("Declaring job")
            self._job_id = self._sched.add_job(self._poll_current_reading, "cron",
            year=time_settings["cron"]["year"], month=time_settings["cron"]["month"],
            day=time_settings["cron"]["day"], week=time_settings["cron"]["week"],
            day_of_week=time_settings["cron"]["day_of_week"], hour=time_settings["cron"]["hour"],
            minute=time_settings["cron"]["minute"], second=time_settings["cron"]["second"]).id
            self.log_message("Initially pausing job")
            self._sched.pause_job(job_id=self._job_id)
        else:
            return False
        return True

    def activate_polling(self):
        self.log_message("Resuming job")
        self._sched.resume_job(job_id=self._job_id)
    def deactivate_polling(self):
        self.log_message("Pausing job")
        self._sched.pause_job(job_id=self._job_id)

    def set_parameter(self, parameter_name, parameter_value):
        raise NotImplementedError
    def get_parameter(self, parameter_name):
        raise NotImplementedError