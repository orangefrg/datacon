from .basic import get_latest_valid_tag, get_range_valid_tag, get_latest_valid_value, get_range_valid_values
from .dataset_getter import query_dataset_latest, query_dataset_latest_n, query_dataset_range
from .tags_getter import query_tags_latest, query_tags_latest_n, query_tags_range, obtain_tags_list
from datetime import datetime, timedelta
import json
from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from datacon.models import DataSource, DataTag, DataSet, Error, ReadingNumeric, ReadingDiscrete, ReadingText
from dateutil import parser

MODE_LATEST = 0
MODE_N_LATEST = 1
MODE_RANGE = 2

DATASET_QUERY = 0
TAGS_QUERY = 1

ABSOLUTE_MAXIMUM_NUMBERS = 500

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
        date_start = parser.parse(request["date_start"])
        if "date_end" in request:
            date_end = parser.parse(request["date_end"])
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
        date_start = parser.parse(request["date_start"])
        if "date_end" in request:
            date_end = parser.parse(request["date_end"])
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

# Input JSON structure:
#
#    dataset - dataset id
#    OR
#    tags - list of dicts:
#       datasource_id - datasource id
#       name - tag name
# ---
#    RANGE MODE
#    date_start (ISO string mandatory) latest timestamp or data needed
#    date_end (ISO string optional default=now) earliest timestamp of data needed
#    max_number (integer optional default=50) maximum number of readings
#    bound_earlier (boolean optional default=True) get closest earlier value in case none are available in range
#    bound_later (boolean optional default=False) get closest later value in case none are available in range
#    LATEST N MODE
#    depth (ISO string mandatory) number of readings needed
# ---
#    COMMON
#    only_valid (boolean optional default=True) retrieve only errorless readings
#    round_numerics (integer optional default=2) number of decimal points
#    get_limits (integer optional deafult=1) 0 - no limits info, 1 - basic info, 2 - detailed info
#    get_trends (list of integers optional default=empty) list of intervals in seconds for which to calculate trends
#    diag_info (boolean optional default=False) get extra diagnostics info

def _validate_parameters(settings):
    mode = MODE_LATEST
    result_parameters = {}
    # Range mode
    if "date_start" in settings:
        mode = MODE_RANGE
        try:
            d_start = parser.parse(settings["date_start"])
        except:
            d_start = datetime.now() - timedelta(seconds=60)
        result_parameters["date_start"] = d_start
        if "date_end" in settings:
            try:
                d_end = parser.parse(settings["date_end"])
            except:
                pass
        if "max_number" in settings:
            try:
                num = int(settings["max_number"])
                if num < 0 or num > ABSOLUTE_MAXIMUM_NUMBERS:
                    num = 50
            except:
                num = 50
            result_parameters["max_number"] = num
        if "bound_eariler" in settings:
            try:
                result_parameters["bound_earlier"] = bool(settings["bound_earlier"])
            except:
                pass
        if "bound_later" in settings:
            try:
                result_parameters["bound_later"] = bool(settings["bound_later"])
            except:
                pass
    # Latest N mode
    elif "depth" in settings:
        mode = MODE_N_LATEST
        try:
            num = int(settings["depth"])
            if num < 0 or num > ABSOLUTE_MAXIMUM_NUMBERS:
                num = 10
        except:
            num = 10
        result_parameters["depth"] = num
    # Common parameters
    if "only_valid" in settings:
        try:
            result_parameters["only_valid"] = bool(settings["only_valid"])
        except:
            pass
    if "round_numerics" in settings:
        try:
            result_parameters["round_numerics"] = int(settings["round_numerics"])
        except:
            pass
    if "get_limits" in settings:
        try:
            result_parameters["get_limits"] = int(settings["get_limits"])
        except:
            pass
    if "get_trends" in settings:
        if isinstance(settings["get_trends"], list):
            result_parameters["get_trends"] = []
            for t in settings["get_trends"]:
                if isinstance(t, int) and t >= 1:
                    result_parameters["get_trends"].append(t)
    if "diag_info" in settings:
        try:
            result_parameters["diag_info"] = bool(settings["diag_info"])
        except:
            pass
    # Getting appropriate mode
    query = None
    if "dataset" in settings:
        result_parameters["dataset_id"] = settings["dataset"]
        query = DATASET_QUERY
    elif "tags" in settings:
        result_parameters["tags"] = []
        query = TAGS_QUERY
        if isinstance(settings["tags"], list):
            for t in settings["tags"]:
                try:
                    result_parameters["tags"].append({
                        "datasource_id": t["datasource_id"],
                        "name": t["name"] 
                    })
                except:
                    pass
    return result_parameters, mode, query

def process_request(request_post):
    stage = "decoding request"
    try:
        result = None
        print(request_post)
        settings = json.loads(request_post["settings"])
        stage = "getting settings"
        kw, mode, query = _validate_parameters(settings)
        if query == DATASET_QUERY:
            if mode == MODE_RANGE:
                result = query_dataset_range(**kw)
            elif mode == MODE_N_LATEST:
                result = query_dataset_latest_n(**kw)
            else:
                result = query_dataset_latest(**kw)
        elif query == TAGS_QUERY:
            tags, pre_result = obtain_tags_list([kw["tags"]])
            kw["tags"] = tags
            if mode == MODE_RANGE:
                result = query_dataset_range(**kw)
            elif mode == MODE_N_LATEST:
                result = query_dataset_latest_n(**kw)
            else:
                result = query_dataset_latest(**kw)
            result["tags"].append(pre_result)
        return result
        
    except Exception as e:
        raise e
        return {"error": {
            "code": 400,
            "reason": "Error on stage: {}".format(stage)
        }}