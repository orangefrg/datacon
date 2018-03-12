from datetime import datetime, timedelta
from datacon.models import ReadingNumeric, ReadingDiscrete, ReadingText, DataTag
from datacon.analysis.trends import get_trend_by_count, get_trend_by_timedelta, get_trend_by_list
from datacon.analysis.limits import get_tag_limits
from django.core.exceptions import ObjectDoesNotExist

LIMITS_NONE = 0
LIMITS_BASIC = 1
LIMITS_DETAILED = 2

# Result of multiple tags query:
#
# time_to_obtain - total time between start and end of data getting
# tag_count - total tag count
# tags - list of results (see below)
# error
#
# 
# tags is a list of dictionaries:
#
# name
# display_name
# units
# error
# readings - list of dictionaries:
# ----
#   reading
#   error (if not only_valid) - TODO
#   timestamp_receive
#   timestamp_packet
#   time_to_obtain (only if diag_info)
#   trends - list of dictionaries (for each seconds value in get_trends)
#   ----
#      period_seconds
#      number
#      direction
#      slope
#      peak_max
#         reading
#         time
#      peak_min
#         reading
#         time
#      average
#         reading
#   ----
#   limits - list of dictionaries (only if get_limits >= LIMITS_BASIC)
#   ----
#      state
#      details (only if get_limits >= LIMITS_DETAILED)
#      ----
#         lower_critical (if exists)
#            reading
#            status
#         lower (if exists)
#            reading
#            status
#         strict (if exists)
#            reading
#            status
#         upper (if exists)
#            reading
#            status
#         upper_critical (if exists)
#            reading
#            status
#      ----
#   ----
# ----
# trend
# -----
#   period_seconds
#   number
#   direction
#   slope
#   peak_max
#      reading
#      time
#   peak_min
#      reading
#      time
#   average
#      reading

def _process_tag(tag,
                 round_numerics=2,
                 only_valid=True,
                 get_limits=LIMITS_BASIC,
                 get_trends=[],
                 diag_info=False,
                 date_start=None,
                 date_end=None,
                 number=None,
                 bound_earlier=True,
                 bound_later=False):
    result = {}
    result["name"] = tag.name
    result["display_name"] = tag.display_name
    result["units"] = tag.units
    readings = []
    if date_start is not None:
        readings = tag.range_of_readings(date_start, date_end, number, only_valid, bound_earlier, bound_later)
    elif number is not None:
        readings = tag.latest_n_readings(number, only_valid)
    else:
        readings = [tag.latest_reading(only_valid)]
    result["readings"] = []
    init_reading = True
    for r in readings:
        rdg = {} 
        if round_numerics is not None and isinstance(r, ReadingNumeric) and r.reading is not None:
            rdg["reading"] = round(r.reading, round_numerics)
        else:
            rdg["reading"] = r.reading
        if r.error is not None:
            rdg["error"] = {}
            rdg["error"]["name"] = r.error.error
            rdg["error"]["description"] = r.error.description
        rdg["timestamp_receive"] = r.timestamp_receive
        rdg["timestamp_packet"] = r.timestamp_packet
        if diag_info:
            rdg["time_to_obtain"] = r.time_to_obtain
        if init_reading:
            init_reading = False
            rdg["trends"] = []
            for t in get_trends:
                trd = get_trend_by_timedelta(r, timedelta(seconds=t))
                rdg["trends"].append(trd)
        if get_limits >= LIMITS_BASIC:
            rdg["limits"] = get_tag_limits(r, get_limits >= LIMITS_DETAILED)
        result["readings"].append(rdg)
    if len(readings) > 1:
        result["trend"] = get_trend_by_list(readings)
    return result
        

# get_trends is valid is following way
# for latest tag trends are calculated for the only reading
# for multiple tag readings trends are calculated for the latest reading
# summary trends are calculated only if there is more than one result

def obtain_tags_list(input_tag_names):
    tags = []
    pre_result = []
    for i in input_tag_names:
        try:
            tags.append(DataTag.objects.get(source__uid=i["datasource"], name=i["name"]))
        except ObjectDoesNotExist:
            pre_result.append({
                "name": i["name"],
                "display_name": i["name"],
                "error": "Tag not found"
            })
    return tags, pre_result


def query_tags_latest(tags,
                    only_valid=True,
                    round_numerics=2,
                    get_limits=LIMITS_BASIC,
                    get_trends=[],
                    diag_info=False):
    t_start = datetime.now()
    result = {
        "tags": []
    }
    for t in tags:
        result["tags"].append(_process_tag(t, round_numerics, only_valid, get_limits, get_trends, diag_info))
    time_to_obtain = (datetime.now() - t_start).total_seconds()
    if round_numerics is not None:
        result["time_to_obtain"] = round(time_to_obtain, round_numerics)
    else:
        result["time_to_obtain"] = time_to_obtain
    result["tag_count"] = len(result["tags"])
    return result


def query_tags_latest_n(tags,
                      depth=50,
                      only_valid=True,
                      round_numerics=2,
                      get_limits=LIMITS_BASIC,
                      get_trends=[],
                      diag_info=False):
    t_start = datetime.now()
    result = {
        "tags": []
    }
    for t in tags:
        result["tags"].append(_process_tag(t, round_numerics, only_valid, get_limits, get_trends, diag_info, number=depth))
    time_to_obtain = (datetime.now() - t_start).total_seconds()
    if round_numerics is not None:
        result["time_to_obtain"] = round(time_to_obtain, round_numerics)
    else:
        result["time_to_obtain"] = time_to_obtain
    result["tag_count"] = len(result["tags"])
    return result

def query_tags_range(tags,
                   date_start,
                   date_end=datetime.now(),
                   max_number=50,
                   only_valid=True,
                   round_numerics=2,
                   get_limits=LIMITS_BASIC,
                   get_trends=[],
                   diag_info=False,
                   bound_earlier=True,
                   bound_later=False):
    t_start = datetime.now()
    result = {
        "tags": []
    }
    for t in tags:
        result["tags"].append(_process_tag(t, round_numerics, only_valid,
                                           get_limits, get_trends, diag_info,
                                           date_start, date_end, max_number,
                                           bound_earlier, bound_later))
    time_to_obtain = (datetime.now() - t_start).total_seconds()
    if round_numerics is not None:
        result["time_to_obtain"] = round(time_to_obtain, round_numerics)
    else:
        result["time_to_obtain"] = time_to_obtain
    result["tag_count"] = len(result["tags"])
    return result

