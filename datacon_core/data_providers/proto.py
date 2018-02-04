import sched, time

# Data provider
# Main abstract class for implementing data collection entities

class Provider:

    def get_name(self):
        raise NotImplementedError
    def get_description(self):
        raise NotImplementedError

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
    # type (required): 'interval' or 'schedule'
    # interval (if interval): interval in seconds (integer)
    # schedule (if schedule): list of tuples (hour, minute, second)
    def activate_polling(self, time_settings):
        raise NotImplementedError
    def deactivate_polling(self):
        raise NotImplementedError

    def set_parameter(self, parameter_name, parameter_value):
        raise NotImplementedError
    def get_parameter(self, parameter_name):
        raise NotImplementedError