from .dataset_getter import get_viewset_range, get_viewset_latest
from .tags_getter import get_tags_latest_by_names, get_tags_range_by_names
from datetime import datetime, timedelta
import json
from uuid import UUID
from dateutil import parser

# TODO: refactor and get rid of waste

LATEST_QUERY = 0
RANGE_QUERY = 1

DATASET_DATA = 0
TAGS_DATA = 1

ABSOLUTE_MAXIMUM_NUMBERS = 500

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


def _determine_mode(settings):
    data_type = None
    query_type = LATEST_QUERY
    if "viewset_id" in settings:
        data_type = DATASET_DATA
    elif "tags" in settings:
        data_type = TAGS_DATA
    for s in ["date_start", "date_end", "number"]:
        if s in settings:
            query_type = RANGE_QUERY
            break
    return data_type, query_type


def _validate_parameters(settings):
    result_parameters = {}
    if "number" in settings:
        try:
            num = int(settings["number"])
            if num < 0 or num > ABSOLUTE_MAXIMUM_NUMBERS:
                num = 50
            result_parameters["number"] = num
        except:
            pass
    if "date_start" in settings:
        try:
            result_parameters["date_start"] = parser.parse(settings["date_start"])
        except:
            pass
    if "date_end" in settings:
        try:
            result_parameters["date_end"] = parser.parse(settings["date_end"])
        except:
            pass
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
    query = None
    if "dataset" in settings:
        result_parameters["viewset_id"] = settings["dataset"]
    elif "tags" in settings:
        result_parameters["tags"] = []
        if isinstance(settings["tags"], list):
            for t in settings["tags"]:
                try:
                    result_parameters["tags"].append({
                        "datasource_id": t["datasource_id"],
                        "name": t["name"] 
                    })
                except:
                    pass
    return result_parameters


def process_request(request_post):
    setting = None
    stage = "decoding request"
    result = None
    try:
        settings = json.loads(request_post["settings"])
        stage = "getting settings"
        params = _validate_parameters(settings)
        data_type, query_type = _determine_mode(params)
        if data_type == DATASET_DATA:
            if query_type == LATEST_QUERY:
                result = get_viewset_latest(**params)
            elif query_type == RANGE_QUERY:
                result = get_viewset_range(**params)
            else:
                stage = "Getting dataset"
                raise Exception("Unknown query type")
        elif data_type == TAGS_DATA:
            if query_type == LATEST_QUERY:
                result = get_tags_latest_by_names(**params)
            elif query_type == RANGE_QUERY:
                result = get_tags_range_by_names(**params)
            else:
                stage = "Getting tags"
                raise Exception("Unknown query type")
        else:
            stage = "Determining data type"
            raise Exception("Unknown data type")
        return result    
    except Exception as e:
        print(e)
        return {"error": {
            "code": 400,
            "reason": "Error on stage: {}".format(stage)
        }}