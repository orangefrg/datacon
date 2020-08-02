from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .receiver.receiver import process_message
from .retriever.request_processor import process_request
from datetime import datetime

import json

@csrf_exempt
def process_incoming(request, source_id):
    if request.method == "POST":
       inc = None
       if request.POST is None or len(request.POST) == 0:
           #ESP32 hack
           inc = json.loads(request.body.decode())
       else:
           inc = request.POST
       process_message(source_id, inc)
    return HttpResponse()

def web_data_view(request, dataset_id):
    template = loader.get_template('web_data_view.html')
    context = {"dataset_id": dataset_id, "page_name": "Data web view", "page_description": "View data online"}
    return HttpResponse(template.render(context, request))

def data_request_core(request):
    if request.method != "POST":
        return HttpResponse(status=400)
    else:
        rsp = process_request(request.POST)
        if "error" in rsp and "code" in rsp and rsp["code"] != 200:
            return HttpResponse(status=rsp["code"])
        else:
            return JsonResponse(rsp)


@csrf_exempt
def data_request(request):
    @csrf_protect
    def foreign_data_request(request):
        return data_request_core(request)

    if request.META["REMOTE_ADDR"] != "127.0.0.1":
        return foreign_data_request(request)
    else:
        return data_request_core(request)

