from datacon.models import DataSource, DataTag, Error, ReadingNumeric, ReadingDiscrete, ReadingText
from django.core.exceptions import ObjectDoesNotExist

from django.http import Http404, HttpResponseBadRequest
from django.utils import timezone
from datetime import datetime

from datacon.retriever.basic import get_latest_valid_tag

import json

def debug_print(message):
    print(type(message), message)

def process_message(datasource, message):
    try:
        ds = DataSource.objects.get(uid=datasource)
    except ObjectDoesNotExist:
        raise Http404
    try:
        msg = json.loads(message["message"])
    except:
        return (400, "Incorrect message")
    write_reading(ds, msg)

def write_reading(datasource, message_as_dict):
    tag_name = message_as_dict["name"]
    for r in message_as_dict["reading"]:
        is_numeric = False
        current_tag = "{}.{}.{}".format(tag_name, r["name"], r["measured_parameter"])
        current_tag_db, was_new = DataTag.objects.get_or_create(source=datasource, name=current_tag)
        if was_new:
            current_tag_db.units = r["units"]
            current_tag_db.save()
        if "error" in r and len(r["error"]) > 0:
            error, was_new = Error.objects.get_or_create(error=r["error"])
        else:
            error = None
        value = r["reading"] if "reading" in r else None
        if isinstance(value, bool):
            parsed_val = value
            rdg_base = ReadingDiscrete.objects
        elif isinstance(value, (int, float)):
            parsed_val = float(value)
            rdg_base = ReadingNumeric.objects
        else:
            try:
                parsed_val = float(value)
                rdg_base = ReadingNumeric.objects
                is_numeric = True
            except ValueError:
                try:
                    parsed_val = int(value)
                    rdg_base = ReadingNumeric.objects
                    is_numeric = True
                except ValueError:
                    parsed_val = value
                    rdg_base = ReadingText.objects
        t_packet_s = datetime.strptime(message_as_dict["start_time"], "%Y-%m-%dT%H:%M:%S.%f")
        t_packet_e = datetime.strptime(message_as_dict["end_time"], "%Y-%m-%dT%H:%M:%S.%f")
        latest = rdg_base.filter(tag=current_tag_db, error=None).latest("timestamp_packet")
        if latest.timestamp_packet.replace(tzinfo=None) < t_packet_e and \
                ((current_tag_db.filter_delta is not None and is_numeric and current_tag_db.filter_delta.delta_value > abs(parsed_val - latest.reading)) or \
                (current_tag_db.ignore_duplicates and latest.reading == parsed_val)):
            print("Dropping value: {} as latest and {} as received".format(latest.reading, parsed_val))
            latest.timestamp_receive = timezone.now()
            latest.save()
        else:
            tto = (t_packet_e - t_packet_s).total_seconds()
            rdg_base.create(tag=current_tag_db, timestamp_packet=t_packet_e, time_to_obtain=tto,
                                    error=error, reading=parsed_val)
    return (200, "Message received")
