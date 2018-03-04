from .basic import get_latest_valid_tag, get_range_valid_tag, get_latest_valid_value, get_range_valid_values
from datetime import datetime
import json
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from datacon.models import DataSource, DataTag, DataSet, Error, ReadingNumeric, ReadingDiscrete, ReadingText


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


def retrieve_dataset(request):
    dataset_id = UUID(request["dataset_id"])
    if "date_start" in request:
        date_start = datetime.strptime(request["date_start"], "%Y-%m-%dT%H:%M:%S.%f")
        if "date_end" in request:
            date_end = datetime.strptime(request["date_end"], "%Y-%m-%dT%H:%M:%S.%f")
            result = get_dataset_range(dataset_id, date_start, date_end)
        else:
            result = get_dataset_range(dataset_id, date_start)
    else:
        result = get_dataset_latest(dataset_id)
    return result
        

def retrieve_single_tag(request):
    datasource_id = UUID(request["datasource_id"])
    tag_name = request["tag_name"]
    if "date_start" in request:
        date_start = datetime.strptime(request["date_start"], "%Y-%m-%dT%H:%M:%S.%f")
        if "date_end" in request:
            date_end = datetime.strptime(request["date_end"], "%Y-%m-%dT%H:%M:%S.%f")
            result = get_range_valid_tag(datasource_id, tag_name, date_start, date_end)
        else:
            result = get_range_valid_tag(datasource_id, tag_name, date_start)
    else:
        result = get_latest_valid_tag(datasource_id, tag_name)
    return result


def retriever_worker(request_post):
    try:
        request_post = json.loads(request_post["message"])
        mode = request_post["mode"]
        if mode == "data_set":
            result = retrieve_dataset(request_post["request"])
        elif mode == "single_tag":
            result = retrieve_single_tag(request_post["request"])
        else:
            return {"error": {
                "code": 400,
                "reason": "Unknown mode"
            }}
    except Exception as e:
        raise e
        return {"error": {
            "code": 400,
            "reason": "Request not recognized"
        }}
    return result
