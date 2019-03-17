from scipy import stats
import numpy as np
from datetime import datetime, timedelta
from datacon.models import ValueNumeric

TREND_LOWER_COUNT = 5

def _get_trends_for_values(values, depth=None):
    trend_info = {}
    if len(values) == 0:
        trend_info["error"] = "No data"
        return trend_info
    elif depth is not None:
        if len(values) <= depth:
            trend_info["error"] = "Low values count"
        else:
            values = values[:depth]
    peaks = sorted(values, key=lambda k: k.value, reverse=True)
    peak_max = peaks[0]
    peak_min = peaks[-1]
    trend_info["peak_max"] = {}
    trend_info["peak_max"]["reading"] = peak_max.value
    trend_info["peak_max"]["time"] = peak_max.timestamp_obtain
    trend_info["peak_min"] = {}
    trend_info["peak_min"]["reading"] = peak_min.value
    trend_info["peak_min"]["time"] = peak_min.timestamp_obtain
    if len(values) <= TREND_LOWER_COUNT:
        trend_info["error"] = "Insufficient values count"
        return trend_info
    latest_np = []
    for v in values:
        latest_np.append((v.timestamp_obtain.timestamp(), v.value))
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


def get_trend_by_age(value, age=timedelta(hours=3)):
    oldest_time = value.timestamp_obtain - age
    latest_n = list(ValueNumeric.objects.filter(tag=value.tag,
                                                timestamp_obtain__lte=value.timestamp_obtain,
                                                timestamp_obtain__gte=oldest_time,
                                                error=None).exclude(value=None).order_by('-timestamp_obtain'))
    trend_info = _get_trends_for_values(latest_n)
    trend_info["period_seconds"] = int(age.total_seconds())
    trend_info["number"] = len(latest_n)
    return trend_info


def get_trend_by_values(values):
    trend_info = _get_trends_for_values(values)
    values = sorted(values, key=lambda k: k.timestamp_obtain, reverse=True)
    trend_info["period_seconds"] = int((values[0].timestamp_obtain - values[-1].timestamp_obtain).total_seconds())
    trend_info["number"] = len(values)
    return trend_info
 