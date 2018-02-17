from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .receiver.receiver import debug_print, process_message
from .retriever.basic import get_tag_value

@csrf_exempt
def echo(request):
    if request.method == "POST":
       debug_print(request.POST)
    return HttpResponse()

@csrf_exempt
def process_incoming(request, source_id):
    if request.method == "POST":
       process_message(source_id, request.POST)
    return HttpResponse()

def get_latest_test(request):
    hum = get_tag_value("Test_home", "GY-21.Main.humidity", "Влажность дома")
    ins = get_tag_value("Test_home", "GY-21.Main.temperature", "Температура дома")
    outs = get_tag_value("Test_home", "DS1.Outside.temperature", "Температура на улице")
    http = "{}<br/>{}<br/>{}".format(outs, ins, hum)
    return HttpResponse(http)

