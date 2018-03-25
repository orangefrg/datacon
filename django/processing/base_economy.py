from datetime import timedelta, datetime
from datacon.models import ReadingNumeric, ReadingDiscrete, ReadingText, DataTag
from datacon.models import ReductionByTime, ReductionByDelta, ReductionByDuplicates
import math

# TODO: Reduction refactoring

# Helps to reduce data count in base
# Gets all data of specific model up to date
# Deletes all data, leaving only "one record at a specified timespan"
# Minimum timespan is a timedelta object

def _reduce_base_by_time(time_back_ago, minimum_timespan, datatag, simulate=False):
    to_reduce = ReadingNumeric.objects.filter(tag=datatag, timestamp_packet__lte=(datetime.now() - time_back_ago)).order_by('timestamp_packet')
    if len(to_reduce) == 0:
        return 0
    to_delete = []
    init_time = to_reduce[0].timestamp_packet
    for r in to_reduce[1:]:
        if r.timestamp_packet < init_time + minimum_timespan and r.error is None:
            to_delete.append(r)
        else:
            init_time = r.timestamp_packet
    cnt = len(to_delete)
    for r in to_delete:
        if not simulate:
            r.delete()
        else:
            print("Deleting: {} ({} @ {}".format(r.tag.name, r.reading, r.timestamp_packet))
    return cnt

def _reduce_base_by_delta(time_back_ago, minimum_delta, datatag, simulate=False):
    to_reduce = ReadingNumeric.objects.filter(tag=datatag, timestamp_packet__lte=(datetime.now() - time_back_ago)).order_by('timestamp_packet')
    if len(to_reduce) == 0:
        return 0
    to_delete = []
    init_value = to_reduce[0].reading
    for r in to_reduce[1:]:
        if minimum_delta > math.fabs(r.reading - init_value):
            to_delete.append(r)
        else:
            init_value = r.reading
    cnt = len(to_delete)
    for r in to_delete:
        if not simulate:
            r.delete()
        else:
            print("Deleting: {} ({} @ {}".format(r.tag.name, r.reading, r.timestamp_packet))
    return cnt

def _reduce_duplicates(model, datatag, simulate=False):
    to_reduce = model.objects.filter(tag=datatag).order_by('timestamp_packet')
    if len(to_reduce) == 0:
        return 0
    to_delete = []
    init_value = to_reduce[0].reading
    for r in to_reduce[1:]:
        if r.reading == init_value:
            to_delete.append(r)
        else:
            init_value = r.reading
    cnt = len(to_delete)
    for r in to_delete:
        if not simulate:
            r.delete()
        else:
            print("Deleting: {} ({} @ {}".format(r.tag.name, r.reading, r.timestamp_packet))
    return cnt

def _reduce_base_by_duplicates(datatag, simulate=False):
    cnt = _reduce_duplicates(ReadingDiscrete, datatag, simulate) + _reduce_duplicates(ReadingText, datatag, simulate) + _reduce_duplicates(ReadingNumeric, datatag, simulate)
    return cnt

# Optimization functions
# These guys obtain scheme from base and convert it to optimized one following rules:
# 1. More aggressive filters can only affect older data.
# 2. Newer and more aggressive one overwrite older ones
# 3. Older ones are applied first
def _optimize_reduction_scheme(scheme):
    for dt, settings in scheme.items():
        if "by_time" in settings:
            active_scheme = []
            max_delta = 0
            for t in settings["by_time"]:
                if t.minimum_timespan > max_delta:
                    max_delta = t.minimum_timespan
                    active_scheme.append(t)
            settings["by_time"] = active_scheme[::-1]
        if "by_delta" in settings:
            active_scheme = []
            max_delta = 0
            for t in settings["by_delta"]:
                if t.minimum_timespan > max_delta:
                    max_delta = t.minimum_timespan
                    active_scheme.append(t)
            settings["by_delta"] = active_scheme[::-1]
    return scheme

def _obtain_reduction_scheme():
    scheme = {}
    for d in DataTag.objects.filter(reductionbytime__isnull=False):
        if d not in scheme:
            scheme[d] = {}
            scheme[d]["by_time"] = []
        for r in d.reductionbytime_set.all().order_by('time_back_ago'):
            scheme[d]["by_time"].append(r)
    for d in DataTag.objects.filter(reductionbydelta__isnull=False):
        if d not in scheme:
            scheme[d] = {}
            scheme[d]["by_delta"] = []
        for r in d.reductionbydelta_set.all().order_by('time_back_ago'):
            scheme[d]["by_delta"].append(r)
    for d in DataTag.objects.filter(reductionbyduplicates__isnull=False):
        if d not in scheme:
            scheme[d] = {}
            scheme[d]["by_duplicates"] = True
            continue
    return _optimize_reduction_scheme(scheme)

def timedelta_to_days(td):
    return float(td.days) + float(td.seconds) / float(86400)

def days_to_timedelta(days):
    return timedelta(days=days)

def reduce_by_scheme(simulate=False):
    print("STARTING REDUCTION")
    t_start = datetime.now()
    reduction = []
    scheme = _obtain_reduction_scheme()
    for dt, settings in scheme.items():
        reduction_count = 0
        if "by_time" in settings:
            for s in settings["by_time"]:
                reduction_count += _reduce_base_by_time(days_to_timedelta(s.time_back_ago), days_to_timedelta(s.minimum_timespan), dt, simulate)
        if "by_delta" in settings:
            for s in settings["by_delta"]:
                reduction_count += _reduce_base_by_delta(days_to_timedelta(s.time_back_ago), s.minimum_delta, dt, simulate)
        if "by_duplicates" in settings and settings["by_duplicates"]:
            reduction_count += _reduce_base_by_duplicates(dt, simulate)
        if reduction_count > 0:
            reduction.append(
                {
                    "tag": dt,
                    "count": reduction_count
                }
            )
    t_elapsed = (datetime.now() - t_start).total_seconds()
    print("BASE REDUCED IN {} s".format(t_elapsed))
    return reduction
