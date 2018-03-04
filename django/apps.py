from django.apps import AppConfig

has_uwsgi = False
try:
    import uwsgi
    has_uwsgi = True
    print("uWSGI launch detected")
except:
    print("WARNING! No uWSGI found")

class DataconConfig(AppConfig):
    name = 'datacon'

    def ready(self):      
        if has_uwsgi:
            from datacon.processing.base_economy import reduce_by_scheme
            print("Standard startup scheme - using uWSGI scheduler")
            uwsgi.register_signal(89, "", reduce_by_scheme)
            uwsgi.add_cron(89, -1, 0, -1, -1, -1)
        else:
            print("Running without UWSGI (reduced functionality)")
