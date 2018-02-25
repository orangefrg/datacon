from datacon.models import DataSource, DataTag, DataSet, Error, ReadingNumeric, ReadingDiscrete, ReadingText
from datetime import datetime, timedelta
from django.core.exceptions import ObjectDoesNotExist
from datacon.analysis.trends import get_trend_by_timedelta
import math

def get_tag_value_test(dsource_name, dtag, description):
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

def get_latest_valid_value(dtag, round_numerics=None, date_end=None, check_alerts=True):
    need_round = False
    kw = {"error": None, "tag": dtag}
    if date_end is not None:
        kw["timestamp_packet__lte"] = date_end
    try:
        latest = ReadingNumeric.objects.filter(**kw).latest('timestamp_packet')
        need_round = round_numerics is not None and isinstance(round_numerics, int)
    except:
        latest = None
    try:
        latest_discrete = ReadingDiscrete.objects.filter(**kw).latest('timestamp_packet')
        if latest is None or latest_discrete.timestamp_packet > latest.timestamp_packet:
            latest = latest_discrete
            need_round = False
    except:
        latest_discrete = None
    try:
        latest_text = ReadingText.objects.filter(**kw).latest('timestamp_packet')
        if latest is None or latest_text.timestamp_packet > latest.timestamp_packet:
            latest = latest_text
            need_round = False
    except:
        latest_text = None
    if latest is not None:
        limits = get_tag_limits(latest)
        trend_3h = get_trend_by_timedelta(latest, timedelta(hours=3))
        trend_24h = get_trend_by_timedelta(latest, timedelta(days=1))
        latest = {"reading": latest.reading if not need_round or latest.reading is None else round(latest.reading, round_numerics),
                "timestamp_packet": latest.timestamp_packet,
                "timestamp_receive": latest.timestamp_receive,
                "time_to_obtain": latest.time_to_obtain,
                "limits": limits,
                "trend_3h": trend_3h,
                "trend_24h": trend_24h}
    else: 
        latest = {"reading": None,
                  "error": "No data"}
    return latest

def get_range_valid_values(dtag, date_start, date_end=datetime.now(), round_numerics=None):
    numerics = ReadingNumeric.objects.filter(error=None, tag=dtag, timestamp_packet__range=(date_start, date_end))
    discretes = ReadingDiscrete.objects.filter(error=None, tag=dtag, timestamp_packet__range=(date_start, date_end))
    text = ReadingText.objects.filter(error=None, tag=dtag, timestamp_packet__range=(date_start, date_end))
    out_objects = []
    num_proc = numerics.values("reading", "timestamp_packet", "timestamp_receive", "time_to_obtain")
    if round_numerics is not None and isinstance(round_numerics, int):
        for n in num_proc:
            if "reading" in n and isinstance(n["reading"], float):
                n["reading"] = round(n["reading"], round_numerics)
    out_objects.extend(num_proc)
    out_objects.extend(discretes.values("reading", "timestamp_packet", "timestamp_receive", "time_to_obtain"))
    out_objects.extend(text.values("reading", "timestamp_packet", "timestamp_receive", "time_to_obtain"))
    return out_objects

def get_latest_valid_tag(datasource_id, tag_name, round_numerics=None):
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
    t_val = get_latest_valid_value(dtag, round_numerics)
    if t_val is not None:
        t_result["reading"].append(t_val)
    else:
        t_result["error"] = "No data"
    out_obj["results"].append(t_result)
    return out_obj

def get_range_valid_tag(datasource_id, tag_name, date_start, date_end=datetime.now(), round_numerics=None):
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
    t_vals = get_range_valid_values(dtag, date_start, date_end, round_numerics)
    if len(t_vals) > 0:
        for v in t_vals:
            t_result["reading"].append(v)
    else:
        t_result["error"] = "No data"
    out_obj["results"].append(t_result)
    return out_obj


def get_dataset_latest(dataset_id, round_numerics=None):
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
        t_val = get_latest_valid_value(t, round_numerics)
        t_result["reading"] = []
        t_result["units"] = t.units
        if t_val is not None:
            t_result["reading"].append(t_val)
        else:
            t_result["error"] = "No data"
        out_obj["results"].append(t_result)
    return out_obj

def get_dataset_range(dataset_id, date_start, date_end=datetime.now(), round_numerics=None):
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
        t_vals = get_range_valid_values(t, date_start, date_end, round_numerics)
        t_result["units"] = t.units
        t_result["reading"] = []
        if len(t_vals) > 0:
            for v in t_vals:
                t_result["reading"].append(v)
        else:
            t_result["error"] = "No data"
        out_obj["results"].append(t_result)
    return out_obj

def get_tag_limits(reading):
    tag = reading.tag
    if hasattr(reading, "alert_values"):
        limits = {}
        if reading.__class__ in [ReadingDiscrete, ReadingNumeric]:
            if tag.alert_values.strict_equal_value is not None:
                up = get_latest_valid_value(tag.alert_values.strict_equal_value, date_end=reading.timestamp_packet, check_alerts=False)
                limit = {"reading": up["reading"]}
                if (isinstance(up["reading"], float) and reading.__class__ == ReadingNumeric) or (isinstance(up["reading"], bool) and reading.__class__ == ReadingDiscrete):
                    if up["reading"] == reading.reading:
                        limit["status"] = "in"
                    else:
                        limit["status"] = "out"
                else:
                    limit["error"] = "Wrong type for limit"
                limits["strict"] = limit

            if reading.__class__ == ReadingNumeric:
                if tag.alert_values.upper_boundary is not None:
                    up = get_latest_valid_value(tag.alert_values.upper_boundary, date_end=reading.timestamp_packet, check_alerts=False)
                    limit = {"reading": up["reading"]}
                    if isinstance(up["reading"], float):
                        if reading.reading > up["reading"]:
                            limit["status"] = "out"
                        elif reading.reading == up["reading"]:
                            limit["status"] = "marginal"
                        else:
                            limit["status"] = "in"
                    else:
                        limit["error"] = "Wrong type for limit"
                    limits["upper"] = limit

                if tag.alert_values.critical_upper_boundary is not None:
                    up = get_latest_valid_value(tag.alert_values.critical_upper_boundary, date_end=reading.timestamp_packet, check_alerts=False)
                    limit = {"reading": up["reading"]}
                    if isinstance(up["reading"], float):
                        if reading.reading > up["reading"]:
                            limit["status"] = "out"
                        elif reading.reading == up["reading"]:
                            limit["status"] = "marginal"
                        else:
                            limit["status"] = "in"
                    else:
                        limit["error"] = "Wrong type for limit"
                    limits["upper_critical"] = limit
                    
                if tag.alert_values.lower_boundary is not None:
                    up = get_latest_valid_value(tag.alert_values.lower_boundary, date_end=reading.timestamp_packet, check_alerts=False)
                    limit = {"reading": up["reading"]}
                    if isinstance(up["reading"], float):
                        if reading.reading > up["reading"]:
                            limit["status"] = "out"
                        elif reading.reading == up["reading"]:
                            limit["status"] = "marginal"
                        else:
                            limit["status"] = "in"
                    else:
                        limit["error"] = "Wrong type for limit"
                    limits["lower"] = limit
                    
                if tag.alert_values.critical_lower_boundary is not None:
                    up = get_latest_valid_value(tag.alert_values.critical_lower_boundary, date_end=reading.timestamp_packet, check_alerts=False)
                    limit = {"reading": up["reading"]}
                    if isinstance(up["reading"], float):
                        if reading.reading > up["reading"]:
                            limit["status"] = "out"
                        elif reading.reading == up["reading"]:
                            limit["status"] = "marginal"
                        else:
                            limit["status"] = "in"
                    else:
                        limit["error"] = "Wrong type for limit"
                    limits["lower_critical"] = limit

        return limits
    return None