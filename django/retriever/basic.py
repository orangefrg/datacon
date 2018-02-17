from datacon.models import DataSource, DataTag, Error, ReadingNumeric, ReadingDiscrete, ReadingText
from datetime import datetime

def get_tag_value(dsource_name, dtag, description):
    ds = DataSource.objects.get(name=dsource_name)
    dtag = DataTag.objects.get(source=ds, name=dtag)
    now = datetime.utcnow()
    try:
        latest = ReadingNumeric.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        val = round(latest.reading, 2)
    except:
        latest = None
    try:
        latest_discrete = ReadingDiscrete.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        if latest is not None and latest_discrete.timestamp_packet > latest.timestamp_packet:
            latest = latest_discrete
            val = latest.reading
    except:
        latest_discrete = None
    try:
        latest_text = ReadingText.objects.filter(error=None, tag=dtag).latest('timestamp_packet')
        if latest is not None and latest_discrete.timestamp_packet > latest.timestamp_packet:
            latest = latest_discrete
            val = latest.reading
    except:
        latest_text = None
    age = now - latest.timestamp_packet.replace(tzinfo=None)
    mins = int(age.total_seconds())//60
    out_str = "{}: {}{} ({} минут назад)".format(description, val, latest.tag.units, mins)
    return out_str
    