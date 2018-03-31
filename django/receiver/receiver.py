from datacon.models import DataSource, Error, TagNumeric, TagDiscrete, TagText
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from datetime import datetime
import json


def process_message(datasource, message):
    try:
        ds = DataSource.objects.get(uid=datasource)
    except ObjectDoesNotExist:
        raise Http404
    try:
        msg = json.loads(message["message"])
    except:
        return (400, "Incorrect message")
    fails = write_reading(ds, msg)
    # TODO: report of failed write attempts
    return (200, "Message received")


def get_or_create_tag(datasource, tag_name, tag_type, units=None):
    if tag_type == "Numeric":
        current_tag_db, was_new = TagNumeric.objects.get_or_create(data_source=datasource, name=tag_name)
        if was_new and units is not None:
            current_tag_db.units = units
            current_tag_db.save
    elif tag_type == "Discrete":
        current_tag_db, was_new = TagDiscrete.objects.get_or_create(data_source=datasource, name=tag_name)
    else:
        current_tag_db, was_new = TagText.objects.get_or_create(data_source=datasource, name=tag_name)
    return current_tag_db


def try_to_save_value(tag, tag_type, value, error=None, timestamp_obtain=datetime.now(), time_to_obtain=0):
    if value is not None and tag_type == "Numeric":
        try:
            parsed_val = float(value)
        except ValueError:
            parsed_val = None
    elif value is not None and tag_type == "Discrete":
        try:
            parsed_val = bool(value)
        except ValueError:
            parsed_val = None
    else:
        parsed_val = value
    tag.values.add_value(parsed_val, error, timestamp_obtain, time_to_obtain)
        

def write_reading(datasource, message_as_dict):
    provider_name = message_as_dict["name"]
    counter_fail = 0
    for r in message_as_dict["reading"]:
        tag_name = "{}.{}.{}".format(provider_name, r["name"], r["measured_parameter"])
        tag_type = r["type"]
        tag_units = None if "units" not in r else r["units"]
        tag = get_or_create_tag(datasource, tag_name, tag_type, tag_units)
        t_packet_s = datetime.strptime(message_as_dict["start_time"], "%Y-%m-%dT%H:%M:%S.%f")
        t_packet_e = datetime.strptime(message_as_dict["end_time"], "%Y-%m-%dT%H:%M:%S.%f")
        time_to_obtain = (t_packet_e - t_packet_s).total_seconds()
        if "error" in r and len(r["error"]) > 0:
            error, was_new = Error.objects.get_or_create(error=r["error"])
        else:
            error = None
        kw = {
            "tag": tag,
            "tag_type": tag_type,
            "error": error,
            "timestamp_obtain": t_packet_e,
            "time_to_obtain": time_to_obtain
        }
        if "reading" in r:
            kw["value"] = r["reading"]
        else:
            kw["value"] = None
        if not try_to_save_value(**kw):
            counter_fail += 1
    return counter_fail
