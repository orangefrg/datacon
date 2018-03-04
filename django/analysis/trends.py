from scipy import stats
import numpy as np
from datetime import datetime, timedelta
from datacon.models import ReadingNumeric

TREND_LOWER_COUNT = 5

def _get_trend(readings, depth=None):
    trend_info = {}
    if readings.count() == 0:
        trend_info["error"] = "No data"
        return trend_info
    peaks = readings.order_by('-reading')
    peak_max = peaks.first()
    peak_min = peaks.last()
    trend_info["peak_max"] = {}
    trend_info["peak_max"]["reading"] = peak_max.reading
    trend_info["peak_max"]["time"] = peak_max.timestamp_packet
    trend_info["peak_min"] = {}
    trend_info["peak_min"]["reading"] = peak_min.reading
    trend_info["peak_min"]["time"] = peak_min.timestamp_packet
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
    wgt = []
    for i in range(1,len(latest_np)):
        wgt.append(latest_np[i][0] - latest_np[i-1][0])
    avg = np.average(latest_np[1:], axis=0, weights=wgt)[1]
    trend_info["average"] = {}
    trend_info["average"]["reading"] = avg
    if p_value < 0.05:
        trend_info["direction"] = "increase" if slope > 0 else "decrease"
    else:
        trend_info["direction"] = "stable"
    trend_info["slope"] = slope
    return trend_info


def get_trend_by_count(reading, depth=50):
    r_class = reading.__class__
    if r_class != ReadingNumeric:
        return None
    latest_n = r_class.objects.filter(tag=reading.tag, error=None, timestamp_packet__lt=reading.timestamp_packet).order_by('-timestamp_packet')
    trend_info = _get_trend(latest_n)
    trend_info["period_seconds"] = int((latest_n[0].timestamp_packet - latest_n[1].timestamp_packet).total_seconds())
    return trend_info

def get_trend_by_timedelta(reading, timedelta=timedelta(hours=3)):
    r_class = reading.__class__
    if r_class != ReadingNumeric:
        return None
    upper_time = reading.timestamp_packet - timedelta
    latest_n = r_class.objects.filter(tag=reading.tag, error=None, timestamp_packet__lt=reading.timestamp_packet,
                                      timestamp_packet__gt=upper_time).order_by('-timestamp_packet')
    trend_info = _get_trend(latest_n)
    trend_info["period_seconds"] = int(timedelta.total_seconds())
    return trend_info
