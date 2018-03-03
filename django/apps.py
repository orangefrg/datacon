from django.apps import AppConfig
from datacon.processing.base_economy import reduce_by_scheme

sch = None
has_uwsgi = False
try:
    import uwsgi
    has_uwsgi = True
except:
    print("WARNING! No UWSGI found")

class DataconConfig(AppConfig):
    name = 'datacon'

    def ready(self):
        if has_uwsgi:
            print("Standart startup scheme!")
            uwsgi.register_signal(89, "", reduce_by_scheme)
            uwsgi.add_cron(89, hour=0)
        else:
            print("Running without UWSGI (reduced functionality)")
