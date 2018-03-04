from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .receiver.receiver import debug_print, process_message
from .retriever.request_processor import retriever_worker, get_dataset_latest, get_dataset_range
from datetime import datetime

import json

def _return_json_or_error(result):
    if "error" in result:
        return HttpResponse(status=result["error"]["code"], reason=result["error"]["reason"])
    else:
        return JsonResponse(result)

@csrf_exempt
def process_incoming(request, source_id):
    if request.method == "POST":
       process_message(source_id, request.POST)
    return HttpResponse()

def latest_dataset(request, dataset_id):
    result = get_dataset_latest(dataset_id, 2)
    if "error" in result:
        return HttpResponse(status=result["error"]["code"], reason=result["error"]["reason"])
    return JsonResponse(result)

def range_dataset(request, dataset_id, date_start, date_end):
    date_start = datetime.fromtimestamp(date_start)
    date_end = datetime.fromtimestamp(date_end)
    result = get_dataset_range(dataset_id, date_start, date_end, 2)
    if "error" in result:
        return HttpResponse(status=result["error"]["code"], reason=result["error"]["reason"])
    return JsonResponse(result)

@csrf_exempt
def retriever_view(request):
    if request.method != "POST":
        return HttpResponse(status=400)
    return _return_json_or_error(retriever_worker(request.POST))

def web_data_view(request, dataset_id):
    template = loader.get_template('web_data_view.html')
    context = {"dataset_id": dataset_id, "page_name": "Data web view", "page_description": "View data online"}
    return HttpResponse(template.render(context, request))
    
    
