from .basic import get_dataset_latest, get_dataset_range, get_latest_valid_tag, get_range_valid_tag
from datetime import datetime
import json
from uuid import UUID


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
