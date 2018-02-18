from datacon.models import DataSource, DataTag, DataSet, Error, ReadingNumeric, ReadingDiscrete, ReadingText
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist

def get_tag_value(dsource_name, dtag, description):
    ds = DataSource.objects.get(name=dsource_name)
    dtag = DataTag.objects.get(source=ds, name=dtag)
    now = datetime.utcnow()
    try:
        latest = ReadingNumeric.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        val = round(latest.reading, 2)
    except:
        latest = None
    try:
        latest_discrete = ReadingDiscrete.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        if latest is not None and latest_discrete.timestamp_packet > latest.timestamp_packet:
            latest = latest_discrete
            val = latest.reading
    except:
        latest_discrete = None
    try:
        latest_text = ReadingText.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        if latest is not None and latest_discrete.timestamp_packet > latest.timestamp_packet:
            latest = latest_discrete
            val = latest.reading
    except:
        latest_text = None
    age = now - latest.timestamp_packet.replace(tzinfo=None)
    mins = int(age.total_seconds())//60
    out_str = "{}: {}{} ({} минут назад)".format(description, val, latest.tag.units, mins)
    return out_str

def get_latest_valid_value(dtag):
    try:
        latest = ReadingNumeric.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
    except:
        latest = None
    try:
        latest_discrete = ReadingDiscrete.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        if latest is None or latest_discrete.timestamp_packet > latest.timestamp_packet:
            latest = latest_discrete
    except:
        latest_discrete = None
    try:
        latest_text = ReadingText.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        if latest is None or latest_text.timestamp_packet > latest.timestamp_packet:
            latest = latest_text
    except:
        latest_text = None
    return latest

def get_range_valid_values(dtag, date_start, date_end=datetime.now()):
    numerics = ReadingNumeric.objects.filter(error=None, tag=dtag, timestamp_packet__range=(date_start, date_end))
    discretes = ReadingDiscrete.objects.filter(error=None, tag=dtag, timestamp_packet__range=(date_start, date_end))
    text = ReadingText.objects.filter(error=None, tag=dtag, timestamp_packet__range=(date_start, date_end))
    out_objects = []
    out_objects.extend(numerics.values("reading", "timestamp_packet", "timestamp_receive", "time_to_obtain"))
    out_objects.extend(discretes.values("reading", "timestamp_packet", "timestamp_receive", "time_to_obtain"))
    out_objects.extend(text.values("reading", "timestamp_packet", "timestamp_receive", "time_to_obtain"))
    return out_objects

def get_latest_valid_tag(datasource_id, tag_name):
    try:
        dtag = DataTag.objects.get(source__uid=datasource_id, name=tag_name)
    except ObjectDoesNotExist:
        return {"error": {
                    "code": 400,
                    "reason": "Corresponding object not found"
                    }
                }
    out_obj = {"results": []}
    t_result = {}
    t_result["name"] = dtag.get_full_name()
    t_result["display_name"] = dtag.display_name
    t_result["reading"] = []
    t_result["units"] = dtag.units
    t_val = get_latest_valid_value(dtag)
    if t_val is not None:
        v_result = {
                "reading": t_val.reading,
                "timestamp_packet": t_val.timestamp_packet,
                "timestamp_receive": t_val.timestamp_receive
        }
        t_result["reading"].append(v_result)
    else:
        t_result["error"] = "No data"
    out_obj["results"].append(t_result)
    return out_obj

def get_range_valid_tag(datasource_id, tag_name, date_start, date_end=datetime.now()):
    try:
        dtag = DataTag.objects.get(source__uid=datasource_id, name=tag_name)
    except ObjectDoesNotExist:
        return {"error": {
                    "code": 400,
                    "reason": "Corresponding object not found"
                    }
                }
    out_obj = {"results": []}
    t_result = {}
    t_result["name"] = dtag.get_full_name()
    t_result["display_name"] = dtag.display_name
    t_result["reading"] = []
    t_result["units"] = dtag.units
    t_vals = get_range_valid_values(dtag, date_start, date_end)
    if len(t_vals) > 0:
        for v in t_vals:
            v_result = {
                "reading": v["reading"],
                "timestamp_packet": v["timestamp_packet"],
                "timestamp_receive": v["timestamp_receive"]
            }
            t_result["reading"].append(v_result)
    else:
        t_result["error"] = "No data"
    out_obj["results"].append(t_result)
    return out_obj


def get_dataset_latest(dataset_id):
    try:
        ds = DataSet.objects.get(uid=dataset_id)
    except ObjectDoesNotExist:
        return {"error": {
                    "code": 400,
                    "reason": "Corresponding object not found"
                    }
                }
    out_obj = {"results": []}
    for t in ds.tags.all():
        t_result = {}
        t_result["name"] = t.get_full_name()
        t_result["display_name"] = t.display_name
        t_val = get_latest_valid_value(t)
        t_result["reading"] = []
        t_result["units"] = t.units
        if t_val is not None:
            v_result = {
                    "reading": t_val.reading,
                    "timestamp_packet": t_val.timestamp_packet,
                    "timestamp_receive": t_val.timestamp_receive
            }
            t_result["reading"].append(v_result)
        else:
            t_result["error"] = "No data"
        out_obj["results"].append(t_result)
    return out_obj

def get_dataset_range(dataset_id, date_start, date_end=datetime.now()):
    try:
        ds = DataSet.objects.get(uid=dataset_id)
    except ObjectDoesNotExist:
        return {"error": {
                    "code": 400,
                    "reason": "Corresponding object not found"
                    }
                }
    out_obj = {"results": []}
    for t in ds.tags.all():
        t_result = {}
        t_result["name"] = t.get_full_name()
        t_result["display_name"] = t.display_name
        t_vals = get_range_valid_values(t, date_start, date_end)
        t_result["units"] = t.units
        t_result["reading"] = []
        if len(t_vals) > 0:
            for v in t_vals:
                v_result = {
                    "reading": v["reading"],
                    "timestamp_packet": v["timestamp_packet"],
                    "timestamp_receive": v["timestamp_receive"]
                }
                t_result["reading"].append(v_result)
        else:
            t_result["error"] = "No data"
        out_obj["results"].append(t_result)
    return out_obj
