from .tags_getter import get_tags_values_latest, get_tags_values_range
from .tags_getter import LIMITS_BASIC, LIMITS_DETAILED, LIMITS_NONE
from django.core.exceptions import ObjectDoesNotExist

from datacon.models import ViewSet

from uuid import UUID
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

def _get_all_tags(viewset_id):
    v_set = None
    vid = UUID(viewset_id)
    try:
        v_set = ViewSet.objects.get(uid=viewset_id)
    except ObjectDoesNotExist:
        return None
    out_tags = []
    out_tags.extend(v_set.tags_numeric.all())
    out_tags.extend(v_set.tags_discrete.all())
    out_tags.extend(v_set.tags_text.all())
    return out_tags


def get_viewset_latest(viewset_id,
                       only_valid=True,
                       round_numerics=2,
                       get_limits=LIMITS_BASIC,
                       get_trends=[],
                       diag_info=False):
    t_start = datetime.now()
    result = {}
    tags = _get_all_tags(viewset_id)
    if tags is None:
        result = {
            "tags": [],
            "tag_count": 0,
            "error": "Invalid ViewSet ID"
        }
    else:
        result = get_tags_values_latest(tags, only_valid, round_numerics,
                                        get_limits, get_trends, diag_info)
    result["time_to_obtain"] = (datetime.now() - t_start).total_seconds()
    return result
    

def get_viewset_range(viewset_id,
                      date_start=None,
                      date_end=None,
                      number=50,
                      only_valid=True,
                      round_numerics=2,
                      get_limits=LIMITS_BASIC,
                      get_trends=[],
                      diag_info=False,
                      bound_earlier=True,
                      bound_later=False):
    t_start = datetime.now()
    result = {}
    tags = _get_all_tags(viewset_id)
    if tags is None:
        result = {
            "tags": [],
            "tag_count": 0,
            "error": "Invalid ViewSet ID"
        }
    else:
        result = get_tags_values_range(tags, date_start, date_end, number,
                                       only_valid, round_numerics, get_limits,
                                       get_trends, diag_info, bound_earlier,
                                       bound_later)
    result["time_to_obtain"] = (datetime.now() - t_start).total_seconds()
    return result
