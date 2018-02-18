from django.urls import path
from django.contrib import admin
from datacon.views import process_incoming, latest_test, latest_dataset, range_dataset, retriever_view

admin.autodiscover()

urlpatterns = [path(r'incoming/<uuid:source_id>', process_incoming, name='process_incoming'),
               path(r'display/<uuid:dataset_id>', latest_dataset, name='latest_dataset'),
               path(r'display/<uuid:dataset_id>/<int:date_start>/<int:date_end>', range_dataset, name='range_dataset'),
               path(r'display/api', retriever_view, name='retriever_view'),
               path(r'check_test', latest_test, name='latest_test')]
