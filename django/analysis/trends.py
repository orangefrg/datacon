from scipy import stats
import numpy as np
from datetime import datetime, timedelta
from datacon.models import ReadingNumeric

TREND_LOWER_COUNT = 5

def _get_trend(readings, depth=None):
    trend_info = {}
    if readings.count() <= TREND_LOWER_COUNT:
        trend_info["error"] = "Less than {} values count".format(TREND_LOWER_COUNT)
        return trend_info
    elif depth is not None and readings.count() <= depth:
        trend_info["caution"] = "Low values count"
    if depth is not None:
        readings = readings[:depth]
    readings = list(readings.values_list("timestamp_packet", "reading"))
    latest_np = []
    for v in readings:
        latest_np.append((v[0].timestamp(), v[1]))
    latest_np = np.array(latest_np)
    slope, intercept, r_value, p_value, std_err = stats.linregress(latest_np)
    if p_value < 0.05:
        trend_info["direction"] = "increase" if slope > 0 else "decrease"
    else:
        trend_info["direction"] = "stable"
    return trend_info


def get_trend_by_count(reading, depth=50):
    r_class = reading.__class__
    if r_class != ReadingNumeric:
        return None
    latest_n = r_class.objects.filter(tag=reading.tag, error=None, timestamp_packet__lt=reading.timestamp_packet).order_by('-timestamp_packet')
    return _get_trend(latest_n)

def get_trend_by_timedelta(reading, timedelta=timedelta(hours=3)):
    r_class = reading.__class__
    if r_class != ReadingNumeric:
        return None
    upper_time = reading.timestamp_packet - timedelta
    latest_n = r_class.objects.filter(tag=reading.tag, error=None, timestamp_packet__lt=reading.timestamp_packet,
                                      timestamp_packet__gt=upper_time).order_by('-timestamp_packet')
    return _get_trend(latest_n)
