from scipy import stats
import numpy as np
from datetime import datetime, timedelta
from datacon.models import ReadingNumeric

TREND_LOWER_COUNT = 5

# TODO: Trends refactoring

def _get_trend(readings, depth=None):
    trend_info = {}
    if len(readings) == 0:
        trend_info["error"] = "No data"
        return trend_info
    peaks = sorted(readings, key=lambda k: k.reading, reverse=True)
    peak_max = peaks[0]
    peak_min = peaks[-1]
    trend_info["peak_max"] = {}
    trend_info["peak_max"]["reading"] = peak_max.reading
    trend_info["peak_max"]["time"] = peak_max.timestamp_packet
    trend_info["peak_min"] = {}
    trend_info["peak_min"]["reading"] = peak_min.reading
    trend_info["peak_min"]["time"] = peak_min.timestamp_packet
    if len(readings) <= TREND_LOWER_COUNT:
        trend_info["error"] = "Less than {} values count".format(TREND_LOWER_COUNT)
        return trend_info
    elif depth is not None and len(readings) <= depth:
        trend_info["caution"] = "Low values count"
    if depth is not None:
        readings = readings[:depth]
    latest_np = []
    for v in readings:
        latest_np.append((v.timestamp_packet.timestamp(), v.reading))
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
    latest_n = list(r_class.objects.filter(tag=reading.tag, error=None, timestamp_packet__lt=reading.timestamp_packet).order_by('-timestamp_packet'))
    trend_info = _get_trend(latest_n)
    trend_info["period_seconds"] = int((latest_n[0].timestamp_packet - latest_n[-1].timestamp_packet).total_seconds())
    trend_info["number"] = len(latest_n)
    return trend_info

def get_trend_by_timedelta(reading, timedelta=timedelta(hours=3)):
    r_class = reading.__class__
    if r_class != ReadingNumeric:
        return None
    upper_time = reading.timestamp_packet - timedelta
    latest_n = list(r_class.objects.filter(tag=reading.tag, error=None, timestamp_packet__lt=reading.timestamp_packet,
                                      timestamp_packet__gt=upper_time).order_by('-timestamp_packet'))
    trend_info = _get_trend(latest_n)
    trend_info["period_seconds"] = int(timedelta.total_seconds())
    trend_info["number"] = len(latest_n)
    return trend_info

def get_trend_by_list(readings):
    num_readings = []
    for r in readings:
        if r.__class__ == ReadingNumeric:
            num_readings.append(r)
    trend_info = _get_trend(readings)
    num_readings = sorted(num_readings, key=lambda k: k.timestamp_packet, reverse=True)
    trend_info["period_seconds"] = int((num_readings[0].timestamp_packet - num_readings[-1].timestamp_packet).total_seconds())
    trend_info["number"] = len(num_readings)
    return trend_info
    
    