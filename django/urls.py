from django.urls import path
from django.contrib import admin
from datacon.views import process_incoming, web_data_view, data_request

admin.autodiscover()

urlpatterns = [path(r'incoming/<uuid:source_id>', process_incoming, name='process_incoming'),
               path(r'display/web/<uuid:dataset_id>', web_data_view, name='web_data_view'),
               path(r'display/webapi', data_request, name='data_request')]
