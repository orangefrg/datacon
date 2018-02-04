import sched, time

# Data provider
# Main abstract class for implementing data collection entities

class Provider:

    def get_name(self):
        raise NotImplementedError
    def get_measured_parameter(self):
        raise NotImplementedError
    def get_description(self):
        raise NotImplementedError
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