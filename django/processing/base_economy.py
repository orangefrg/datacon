from datetime import timedelta, datetime
from datacon.models import ReductionTimeBased, TagNumeric, TagText, TagDiscrete
import math

def _reduce_tag(tag, time_ago, minimum_timespan, simulate=False):
    latest_value = datetime.now() - time_ago
    values = tag.values(timestamp_obtain__lte=latest_value).order_by['timestamp_obtain']
    init_time = values[0].timestamp_obtain
    to_delete = []
    for v in values[1:]:
        if v.timestamp_obtain < init_time + minimum_timespan:
            to_delete.append(v)
        else:
            init_time = v.timestamp_obtain
    cnt = len(to_delete)
    for v in to_delete:
        if not simulate:
            v.delete()
        else:
            print("SIM: delete {} ({} @ {})".format(v.tag.name, v.value, v.timestamp_obtain))
    return cnt


# Optimization function
# It obtain schemes from base and convert it to optimized ones using following rules:
# 1. More aggressive filters (with higher minimum_timespan) should have higher time_back_ago
# 2. In case of two filters with same time_back_ago, less aggressive one is selected

def _obtain_schemes():
    schemes = {}
    tags_list = []
    tags_list.extend(list(TagNumeric.objects.all()))
    tags_list.extend(list(TagText.objects.all()))
    tags_list.extend(list(TagDiscrete.objects.all()))
    for t in tags_list:
        if hasattr(t, "timebased_reduced_by") and t.timebased_reduced_by.count() > 0:
            sch = []
            for i in t.timebased_reduced_by.all().order_by("time_back_ago", "-minimum_timespan"):
                sch.append(i)
            sch_t = tuple(sch)
            if sch_t not in schemes:
                schemes[sch_t] = {}
                schemes[sch_t]["tags"] = []
                filters = []
                time_back_ago = 0
                minimum_timespan = 0
                for s in sch:
                    if s.time_back_ago > time_back_ago and s.minimum_timespan > minimum_timespan:
                        filters.append(s)
                        time_back_ago = s.time_back_ago
                        minimum_timespan = s.minimum_timespan
                schemes[sch_t]["filters"] = filters.reverse()
            schemes[sch_t]["tags"].append(t)
    return schemes
                

def reduce_by_scheme(simulate=False):
    schemes = _obtain_schemes()
    reduction = []
    for sch, settings in schemes.items():
        for t in settings["tags"]:
            reduct = {}
            reduct["tag"] = t.name
            reduct["datasource"] = t.data_source.uid
            cnt = 0
            for f in settings["filters"]:
                time_ago = timedelta(days=f.time_back_ago)
                minimum_timespan = timedelta(seconds=f.minimum_timespan)
                cnt += _reduce_tag(t, time_ago, minimum_timespan)
            reduct["count"] = cnt
            reduction.append(reduct)
    return reduction
