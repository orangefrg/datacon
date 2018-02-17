from django.urls import path
from django.contrib import admin
from datacon.views import echo, process_incoming, get_latest_test

admin.autodiscover()

urlpatterns = [path(r'incoming/user_one', echo, name='echo'),
               path(r'incoming/<uuid:source_id>', process_incoming, name='process_incoming'),
               path(r'check_test', get_latest_test, name='get_latest_test')]
