from datetime import datetime
from datacon.models import ReadingNumeric, ReadingDiscrete, ReadingText

LIMITS_NONE = 0
LIMITS_BASIC = 1
LIMITS_DETAILED = 2

# Reading result
# List of dictionaries:
# name
# display_name
# units
# reading - list of dictionaries:
# ----
#   reading
#   timestamp_receive
#   timestamp_packet (only if diag_info)
#   time_to_obtain (only if diag_info)
#   trends - list of dictionaries (for each seconds value in get_trends)
#   ----
#      period_seconds
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



def get_tags_latest(tags,
                    only_valid=True,
                    round_numerics=2,
                    get_limits=LIMITS_BASIC,
                    get_trends=[],
                    diag_info=False):
    kw = {"tag__in": tags}
    if only_valid:
        kw["error"] = None
    values_num = ReadingNumeric.objects.filter(**kw).order_by('-timestamp_packet')
    values_dis = ReadingDiscrete.objects.filter(**kw).order_by('-timestamp_packet')
    values_text = ReadingText.objects.filter(**kw).order_by('-timestamp_packet')
    pre_result = {}
    for t in tags:
        for v in values_num:
            if v.tag == t:
                pre_result[t] = v
                break
        for v in values_dis:
            if v.tag == t:
                if t not in pre_result or v.timestamp_packet > pre_result[t].timestamp_packet:
                    pre_result[t] = v
                break
        for v in values_text:
            if v.tag == t:
                if t not in pre_result or v.timestamp_packet > pre_result[t].timestamp_packet:
                    pre_result[t] = v
                break
    

    pass

def get_tags_latest_n(tags,
                      depth=50,
                      only_valid=True,
                      round_numerics=2,
                      get_limits=LIMITS_BASIC,
                      get_trends=[],
                      diag_info=False):
    pass

def get_tags_range(tags,
                   date_start,
                   date_end=datetime.now(),
                   only_valid=1,
                   round_numerics=2,
                   get_limits=LIMITS_BASIC,
                   get_trends=[],
                   diag_info=False):
    pass

