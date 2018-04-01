from datetime import datetime, timedelta
from datacon.models import TagNumeric, TagDiscrete, TagText
from datacon.analysis.trends import get_trend_by_age, get_trend_by_values
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
#            readingget_trend_by_count
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

def _find_tags(input_tag_names):
    tags = []
    missing_tags = []
    for i in input_tag_names:
        found = False
        for t in [TagDiscrete, TagNumeric, TagText]:
            try:
                tags.append(t.objects.get(data_source__uid=i["datasource"], name=i["name"]))
                found = True
                break
            except ObjectDoesNotExist:
                pass
        if not found:
            missing_tags.append({
                "name": i["name"],
                "display_name": i["name"],
                "error": "Tag not found"
            })
    return tags, missing_tags


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
    if hasattr(tag, "units") and tag.units is not None:
        result["units"] = tag.units
    readings = []
    if date_start is not None or number is not None:
        readings = tag.get_range_of_values(date_start=date_start, date_end=date_end, only_valid=only_valid, max_number=number, bound_earlier=bound_earlier)
    else:
        readings = tag.get_latest_value(only_valid)
    result["readings"] = []
    # Trends are needed only for numeric tags
    init_reading = isinstance(tag, TagNumeric)
    for r in readings:
        rdg = {}
        if round_numerics is not None and isinstance(tag, TagNumeric) and r.value is not None:
            rdg["reading"] = round(r.value, round_numerics)
        else:
            rdg["reading"] = r.value
        if r.error is not None:
            rdg["error"] = {}
            rdg["error"]["name"] = r.error.error
            rdg["error"]["description"] = r.error.description
        rdg["timestamp_receive"] = r.timestamp_update
        rdg["timestamp_packet"] = r.timestamp_obtain
        if diag_info:
            rdg["time_to_obtain"] = r.time_to_obtain
        if init_reading:
            init_reading = False
            rdg["trends"] = []
            for t in get_trends:
                trd = get_trend_by_age(r, timedelta(seconds=t))
                rdg["trends"].append(trd)
        if get_limits >= LIMITS_BASIC:
            rdg["limits"] = get_tag_limits(r, get_limits >= LIMITS_DETAILED)
        result["readings"].append(rdg)
    if isinstance(tag, TagNumeric) and len(readings) > 1:
        result["trend"] = get_trend_by_values(readings)
    return result

# get_trends is valid is following way
# for latest tag trends are calculated for the only reading
# for multiple tag readings trends are calculated for the latest reading
# summary trends are calculated only if there is more than one result

def get_tags_values_latest(tags,
                           only_valid=True,
                           round_numerics=2,
                           get_limits=LIMITS_BASIC,
                           get_trends=[],
                           diag_info=False):
    t_start = datetime.now()
    result = {
        "tags": [],
        "tag_count": len(tags)
    }
    if len(tags) == 0:
        result["error"] = "No tags"
    else:
        for t in tags:
            result["tags"].append(_process_tag(t, round_numerics, only_valid, get_limits, get_trends, diag_info))
    time_to_obtain = (datetime.now() - t_start).total_seconds()
    if round_numerics is not None:
        result["time_to_obtain"] = round(time_to_obtain, round_numerics)
    else:
        result["time_to_obtain"] = time_to_obtain
    result["tag_count"] = len(result["tags"])
    return result


def get_tags_values_range(tags,
                          date_start=None,
                          date_end=datetime.now(),
                          number=50,
                          only_valid=True,
                          round_numerics=2,
                          get_limits=LIMITS_BASIC,
                          get_trends=[],
                          diag_info=False,
                          bound_earlier=True,
                          bound_later=False):
    t_start = datetime.now()
    result = {
        "tags": [],
        "tag_count": len(tags)
    }
    if len(tags) == 0:
        result["error"] = "No tags"
    else:
        for t in tags:
            result["tags"].append(_process_tag(t, round_numerics, only_valid,
                                               get_limits, get_trends, diag_info,
                                               date_start, date_end, number,
                                               bound_earlier, bound_later))
    time_to_obtain = (datetime.now() - t_start).total_seconds()
    if round_numerics is not None:
        result["time_to_obtain"] = round(time_to_obtain, round_numerics)
    else:
        result["time_to_obtain"] = time_to_obtain
    result["tag_count"] = len(result["tags"])
    return result


def get_tags_latest_by_names(tags,
                             only_valid=True,
                             round_numerics=2,
                             get_limits=LIMITS_BASIC,
                             get_trends=[],
                             diag_info=False):
    tags_db, missing = _find_tags(tags)
    result = get_tags_values_latest(tags_db, only_valid,
                                    round_numerics, get_limits,
                                    get_trends, diag_info)
    if len(missing) > 0:
        result["tags"].extend(missing)
    return result


def get_tags_range_by_names(tags,
                            date_start=None,
                            date_end=datetime.now(),
                            number=50,
                            only_valid=True,
                            round_numerics=2,
                            get_limits=LIMITS_BASIC,
                            get_trends=[],
                            diag_info=False,
                            bound_earlier=True,
                            bound_later=False):
    tags_db, missing = _find_tags(tags)
    result = get_tags_values_range(tags_db, date_start, date_end,
                                   number, only_valid, round_numerics,
                                   get_limits, get_trends, diag_info,
                                   bound_earlier, bound_later)
    if len(missing) > 0:
        result["tags"].extend(missing)
    return result
