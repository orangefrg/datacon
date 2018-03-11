from datacon.models import ReadingDiscrete, ReadingNumeric
from datacon.retriever.basic import get_latest_valid_value

def get_tag_limits(reading, detailed=False):
    tag = reading.tag
    c_up = None
    n_up = None
    strict = None
    n_dn = None
    c_dn = None
    if hasattr(tag, "alert_values"):
        limits = {}
        if reading.__class__ in [ReadingDiscrete, ReadingNumeric]:
            if tag.alert_values.strict_equal_value is not None:
                up = get_latest_valid_value(tag.alert_values.strict_equal_value, date_end=reading.timestamp_packet, check_alerts=False)
                limit = {"reading": up["reading"]}
                if (isinstance(up["reading"], float) and reading.__class__ == ReadingNumeric) or (isinstance(up["reading"], bool) and reading.__class__ == ReadingDiscrete):
                    if up["reading"] == reading.reading:
                        limit["status"] = "in"
                    else:
                        limit["status"] = "out"
                else:
                    limit["error"] = "Wrong type for limit"
                limits["strict"] = limit

            if reading.__class__ == ReadingNumeric:
                for lm in [(tag.alert_values.upper_boundary, "upper"),
                           (tag.alert_values.critical_upper_boundary, "upper_critical")]:
                    if lm[0] is not None:
                        up = get_latest_valid_value(lm[0], date_end=reading.timestamp_packet, check_alerts=False)
                        limit = {"reading": up["reading"]}
                        if isinstance(up["reading"], float):
                            if reading.reading > up["reading"]:
                                limit["status"] = "out"
                            elif reading.reading == up["reading"]:
                                limit["status"] = "marginal"
                            else:
                                limit["status"] = "in"
                        else:
                            limit["error"] = "Wrong type for limit"
                        limits[lm[1]] = limit
                
                for lm in [(tag.alert_values.lower_boundary, "lower"),
                           (tag.alert_values.critical_lower_boundary, "lower_critical")]:
                    if lm[0] is not None:
                        up = get_latest_valid_value(lm[0], date_end=reading.timestamp_packet, check_alerts=False)
                        limit = {"reading": up["reading"]}
                        if isinstance(up["reading"], float):
                            if reading.reading < up["reading"]:
                                limit["status"] = "out"
                            elif reading.reading == up["reading"]:
                                limit["status"] = "marginal"
                            else:
                                limit["status"] = "in"
                        else:
                            limit["error"] = "Wrong type for limit"
                        limits[lm[1]] = limit
        c_up = limits["upper"]["status"] if "upper" in limits else None
        n_up = limits["upper_critical"]["status"] if "upper_critical" in limits else None
        n_dn = limits["lower"]["status"] if "lower" in limits else None
        c_dn = limits["lower_critical"]["status"] if "lower_critical" in limits else None
        strict = limits["strict"]["status"] if "strict" in limits else None
        res = "normal"
        if c_up == "out":
            res = "very_high"
        elif c_dn == "out":
            res = "very_low"
        elif strict == "out":
            res = "abnormal"
        elif n_up == "out":
            res = "high"
        elif n_dn == "out":
            res = "low"
        result = {}
        result["state"] = res
        if detailed:
            result["details"] = limits
        return result
    return None