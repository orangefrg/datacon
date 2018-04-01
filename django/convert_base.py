from datacon.models import DataTag, DataSet, ReadingNumeric, ReadingDiscrete, ReadingText
from datacon.models import TagNumeric, TagDiscrete, TagText, ViewSet, InputFiltering, ValueDiscrete, ValueNumeric, ValueText
from django.core.exceptions import ObjectDoesNotExist

def clear_tags():
    for t in [TagNumeric, TagDiscrete, TagText]:
        t.objects.all().delete()


def clear_records():
    for r in [ValueDiscrete, ValueNumeric, ValueText]:
        r.objects.all().delete()

def clear_viewsets():
    ViewSet.objects.all().delete()


def make_tags():
    for dt in DataTag.objects.all():
        print("Copying {}".format(dt.name))
        tag_type = None
        input_filter = None
        numeric_count = ReadingNumeric.objects.filter(tag=dt).count()
        text_count = ReadingText.objects.filter(tag=dt).count()
        discr_count = ReadingDiscrete.objects.filter(tag=dt).count()
        mx = max(numeric_count, text_count, discr_count)
        if mx == numeric_count:
            tag_type = TagNumeric
        elif mx == discr_count:
            tag_type = TagDiscrete
        else:
            tag_type = TagText
        new_tag = tag_type(data_source=dt.source,
                           name=dt.name,
                           display_name=dt.display_name,
                           ignore_duplicates=dt.ignore_duplicates)
        if tag_type == TagNumeric:
            new_tag.units = dt.units
            if dt.filter_delta is not None:
                new_tag.input_filter = InputFiltering.objects.create(deadband=dt.filter_delta.delta_value)
        new_tag.save()


def make_records():
    total = 0
    for t in [(TagNumeric, ReadingNumeric, ValueNumeric),
              (TagDiscrete, ReadingDiscrete, ValueDiscrete),
              (TagText, ReadingText, ValueText)]:
        for dt in t[0].objects.all():
            print("Processing tag {} ({} reading by now)".format(dt.name, total))
            vals = t[1].objects.filter(tag__name=dt.name, tag__source=dt.data_source).order_by('timestamp_packet')
            print("Has {} readings".format(len(vals)))
            for v in vals:
                kw = {
                    "timestamp_obtain": v.timestamp_packet,
                    "timestamp_receive": v.timestamp_receive,
                    "timestamp_update": v.timestamp_receive,
                    "time_to_obtain": v.time_to_obtain,
                    "error": v.error,
                    "tag": dt,
                    "value": v.reading
                }
                t[2].objects.create(**kw)
                total += 1
    print("Total {} readings".format(total))


def make_viewsets():
    for ds in DataSet.objects.all():
        kw = {
            "uid": ds.uid,
            "user": ds.user,
            "name": ds.name,
        }
        print("Making viewset {}".format(ds.name))
        vs = ViewSet.objects.create(**kw)
        for t in ds.tags.all():
            print("Adding tag {}".format(t.name))
            try:
                dt = TagNumeric.objects.get(data_source=t.source, name=t.name)
                vs.tags_numeric.add(dt)
            except ObjectDoesNotExist:
                try:
                    dt = TagDiscrete.objects.get(data_source=t.source, name=t.name)
                    vs.tags_discrete.add(dt)
                except ObjectDoesNotExist:
                    try:
                        dt = TagText.objects.get(data_source=t.source, name=t.name)
                        vs.tags_text.add(dt)
                    except ObjectDoesNotExist:
                        pass
        vs.save()
