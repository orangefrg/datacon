from django.urls import path
from django.contrib import admin
from datacon.views import process_incoming, latest_dataset, range_dataset, retriever_view, web_data_view, data_request, repeater

admin.autodiscover()

urlpatterns = [path(r'incoming/<uuid:source_id>', process_incoming, name='process_incoming'),
               path(r'display/<uuid:dataset_id>', latest_dataset, name='latest_dataset'),
               path(r'display/<uuid:dataset_id>/<int:date_start>/<int:date_end>', range_dataset, name='range_dataset'),
               path(r'display/web/<uuid:dataset_id>', web_data_view, name='web_data_view'),
               path(r'display/webapi', data_request, name='data_request'),
               path(r'display/popoogay', repeater, name='repeater'),
               path(r'display/api', retriever_view, name='retriever_view')]
