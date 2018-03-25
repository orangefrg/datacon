from .tags_getter import query_tags_range, query_tags_latest, query_tags_latest_n
from .tags_getter import LIMITS_BASIC, LIMITS_DETAILED, LIMITS_NONE
from django.core.exceptions import ObjectDoesNotExist

from datacon.models import DataSet

from datetime import datetime
# TODO: DataSet refactoring

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


def query_dataset_latest(dataset_id,
                    only_valid=True,
                    round_numerics=2,
                    get_limits=LIMITS_BASIC,
                    get_trends=[],
                    diag_info=False):
    try:
        print(dataset_id)
        ds = DataSet.objects.get(uid=dataset_id)
    except:
        result = {}
        result["error"] = "Dataset not found"
        return result
    return query_tags_latest(ds.tags.all(), only_valid, round_numerics, get_limits, get_trends, diag_info)
    

def query_dataset_latest_n(dataset_id,
                      depth=50,
                      only_valid=True,
                      round_numerics=2,
                      get_limits=LIMITS_BASIC,
                      get_trends=[],
                      diag_info=False):
    try:
        ds = DataSet.objects.get(uid=dataset_id)
    except:
        result = {}
        result["error"] = "Dataset not found"
        return result
    return query_tags_latest_n(ds.tags.all(), depth, only_valid, round_numerics, get_limits, get_trends, diag_info)

def query_dataset_range(dataset_id,
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
    try:
        ds = DataSet.objects.get(uid=dataset_id)
    except:
        result = {}
        result["error"] = "Dataset not found"
        return result
    return query_tags_range(ds.tags.all(), date_start, date_end, max_number,
                            only_valid, round_numerics, get_limits, get_trends, diag_info,
                            bound_earlier, bound_later)