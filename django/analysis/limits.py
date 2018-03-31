from datacon.models import ReadingDiscrete, ReadingNumeric
from datacon.retriever.basic import get_latest_valid_value

def get_tag_limits(value, detailed=False, by_value_date=False):
    if value.value is None:
        return {"error": "Value is none"}
    tag = value.tag
    up_alert = None
    up_value = None
    c_up_alert = None
    c_up_value = None
    lw_alert = None
    lw_value = None
    c_lw_alert = None
    c_lw_value = None
    strict_alert = None
    strict_values = []
    limits = {}
    # Collecting all limits
    if hasattr(tag, "limits"):
        for l in tag.limits.all():
            if by_value_date:
                limits.append(l.get_boundaries(by_date=value.timestamp_obtain))
            else:
                limits.append(l.get_boundaries())
    if hasattr(tag, "strict_values"):
        for l in tag.strict_values.all():
            if by_value_date:
                limits.append({"strict": l.get_value(by_date=value.timestamp_obtain)})
            else:
                limits.append({"strict": l.get_value()})
    # Setting most strict limits
    for l in limits:
        if "critical_upper" in l and (c_up_value is None or c_up_value < l["critical_upper"]):
            c_up_value = l["critical_upper"]
        if "upper" in l and (up_value is None or up_value < l["upper"]) and (c_up_value is None or c_up_value > l["upper"]):
            up_value = l["upper"]
        if "critical_lower" in l and (c_lw_value is None or c_lw_value > l["critical_lower"]):
            c_lw_value = l["critical_lower"]
        if "lower" in l and (lw_value is None or lw_value > l["lower"]) and (c_lw_value is None or c_lw_value < l["lower"]):
            lw_value = l["lower"]
        if "strict" in l and l["strict"] not in strict_values:
            strict_values.append(l["strict"])
    # Checking limits
    if c_up_value is not None:
        c_up_alert = True
        if value.value > c_up_value:
            status = "out"
        elif value.value == c_up_value:
            status = "marginal"
        else:
            status = "in"
            c_up_alert = False
        limits["critical_upper"] = {
            "reading": c_up_value,
            "status": status
        }
    if up_value is not None:
        up_alert = True
        if value.value > up_value:
            status = "out"
        elif value.value == up_value:
            status = "marginal"
        else:
            status = "in"
            up_alert = False
        limits["upper"] = {
            "reading": up_value,
            "status": status
        }
    if c_lw_value is not None:
        c_lw_alert = True
        if value.value < c_lw_value:
            status = "out"
        elif value.value == c_lw_value:
            status = "marginal"
        else:
            status = "in"
            c_lw_alert = False
        limits["critical_lower"] = {
            "reading": c_lw_value,
            "status": status
        }
    if lw_value is not None:
        lw_alert = True
        if value.value < lw_value:
            status = "out"
        elif value.value == lw_value:
            status = "marginal"
        else:
            status = "in"
            lw_alert = False
        limits["lower"] = {
            "reading": lw_value,
            "status": status
        }
    for s in strict_values:
        strict_alert = False
        if value.value != s:
            limits["strict"] = {
                "reading": s,
                "status": "out"
            }
            strict_alert = True
            break
    if strict_alert == False:
        limits["strict"] = {
            "reading": value.value,
            "status": "in"
        }

    # Summarizing...
    res = "normal"
    if c_up_alert:
        res = "very_high"
    elif c_lw_alert == "out":
        res = "very_low"
    elif strict_alert == "out":
        res = "abnormal"
    elif up_alert == "out":
        res = "high"
    elif lw_alert == "out":
        res = "low"
    result = {}
    result["state"] = res
    if detailed:
        result["details"] = limits
    return result
    