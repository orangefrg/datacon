import sched, time
from apscheduler.schedulers.background import BackgroundScheduler

# Data provider
# Main abstract class for implementing data collection entities

class Provider:

    def __init__(self, name, description, scheduler=None):
        self._sched = scheduler or BackgroundScheduler()
        self._name = name
        self._description = description

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

    # Activate and deactivate scheduled data retrieval
    # time_settings is a dict with following fields:
    # interval: interval in seconds (integer)
    # cron: dict of cron values -
    # year, month, day, week, day_of_week, hour, minute, second
    # if both delay and cron are passed, the delay will be used
    # collectors is a list of data collectors
    def _poll_current_reading(self, collectors):
        collectors[0].upload_data(self.get_current_reading(), collectors[1:] if len(collectors) > 0 else None)
    def set_polling(self, time_settings, collectors):

        if "delay" in time_settings:
            self._sched.add_job(self._poll_current_reading, "interval", kwargs={'collectors': collectors}, seconds=time_settings["delay"])

        elif "cron" in time_settings:
            for p in ["year", "month", "day", "week", "day_of_week", "hour", "minute", "second"]:
                if p not in time_settings["cron"]:
                    time_settings["cron"][p] = None
            self._sched.add_job(self._poll_current_reading, "cron", kwargs={'collectors': collectors},
            year=time_settings["cron"]["year"], month=time_settings["cron"]["month"],
            day=time_settings["cron"]["day"], week=time_settings["cron"]["week"],
            day_of_week=time_settings["cron"]["day_of_week"], hour=time_settings["cron"]["hour"],
            minute=time_settings["cron"]["minute"], second=time_settings["cron"]["second"])
        else:
            return False
        self._sched.start(paused=True)
        return True

    def activate_polling(self):
        self._sched.resume()
    def deactivate_polling(self):
        self._sched.pause()

    def set_parameter(self, parameter_name, parameter_value):
        raise NotImplementedError
    def get_parameter(self, parameter_name):
        raise NotImplementedError