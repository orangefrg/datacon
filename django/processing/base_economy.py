from datetime import timedelta, datetime
from datacon.models import ReadingNumeric, ReadingDiscrete, ReadingText
import math

# Helps to reduce data count in base
# Gets all data of specific model up to date
# Deletes all data, leaving only "one record at a specified timespan"
# Minimum timespan is a timedelta object

def reduce_base_by_time(time_back_ago, minimum_timespan, datatag):
    to_reduce = ReadingNumeric.objects.filter(tag=datatag, timestamp_packet__lte=(datetime.now() - time_back_ago)).order_by('-timestamp_packet')
    if len(to_reduce) == 0:
        return 0
    to_delete = []
    init_time = to_reduce[0].timestamp_packet
    for r in to_reduce:
        if r.timestamp_packet > init_time - minimum_timespan and r.error is None:
            to_delete.append(r)
        else:
            init_time = r.timestamp_packet
    cnt = len(to_delete)
    for r in to_delete:
        r.delete()
    return cnt

def reduce_base_by_delta(time_back_ago, minimum_delta, datatag):
    to_reduce = ReadingNumeric.objects.filter(tag=datatag, timestamp_packet__lte=(datetime.now() - time_back_ago)).order_by('-timestamp_packet')
    if len(to_reduce) == 0:
        return 0
    to_delete = []
    init_value = to_reduce[0].reading
    for r in to_reduce:
        if minimum_delta > math.fabs(r.value - init_value):
            to_delete.append(r)
        else:
            init_value = r.value
    cnt = len(to_delete)
    for r in to_delete:
        r.delete()
    return cnt

def _reduce_duplicates(model, datatag):
    to_reduce = model.objects.filter(tag=datatag).order_by('-timestamp_packet')
    if len(to_reduce) == 0:
        return 0
    to_delete = []
    init_value = to_reduce[0].reading
    for r in to_reduce:
        if r.value == init_value:
            to_delete.append(r)
        else:
            init_value = r.value
    cnt = len(to_delete)
    for r in to_delete:
        r.delete()
    return cnt

def reduce_base_by_duplicates(datatag):
    cnt = _reduce_duplicates(ReadingDiscrete, datatag) + _reduce_duplicates(ReadingText, datatag)
    return cnt

# Scheme is a list of dicts
# Dict structure:
# "source" - uid of data source
# "tagname" - name of tag to reduce
# "by_time" - dict:
#       "time_back_ago" - timedelta object. Reduction will be applied for readings older than now minus time_back_ago
#       "minimum_timespan" - timedelta object. Readings will be reduced to this minimal time interval
# "by_delta" - dict:
#       "time_back_ago" - timedelta object. Reduction will be applied for readings older than now minus time_back_ago
#       "minimum_delta" - timedelta object. Readings will be reduced in case difference between their value and last value is less than delta
# "by_duplicates" - a key with any value. Duplicates will be reduced.
def reduce_base_by_scheme(scheme):
    # Here dictionary should be optimized in such way:
    # For each tag, reduction with older filtering should be applied
    # If any newer filtering with more aggressive reduction is present, older one should be ignored
    pass
