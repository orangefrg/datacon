from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .receiver.receiver import process_message
from .retriever.request_processor import process_request
from datetime import datetime

import json

@csrf_exempt
def process_incoming(request, source_id):
    if request.method == "POST":
       process_message(source_id, request.POST)
    return HttpResponse()

def web_data_view(request, dataset_id):
    template = loader.get_template('web_data_view.html')
    context = {"dataset_id": dataset_id, "page_name": "Data web view", "page_description": "View data online"}
    return HttpResponse(template.render(context, request))

def data_request(request):
    if request.method != "POST":
        return HttpResponse(status=400)
    else:
        rsp = process_request(request.POST)
        if "error" in rsp and "code" in rsp and rsp["code"] != 200:
            return HttpResponse(status=rsp["code"])
        else:
            return JsonResponse(rsp)


    
    
