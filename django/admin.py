from django.contrib import admin

from .models import DataSource, DataTag, Error, DataSet
from .models import ReadingDiscrete, ReadingNumeric, ReadingText, AlertValues
from .models import ReductionByTime, ReductionByDelta, ReductionByDuplicates, FilterDelta
from .models import InputFiltering, TagNumeric, TagDiscrete, TagText, TagNumericLimits, TagStrictValueNumeric, TagStrictValueDiscrete, TagStrictValueText
from .models import ValueNumeric, ValueDiscrete, ValueText, ViewSet, ReductionTimeBased

admin.site.register(DataSource)
admin.site.register(DataSet)
admin.site.register(DataTag)
admin.site.register(Error)
admin.site.register(AlertValues)
admin.site.register(ReadingDiscrete)
admin.site.register(ReadingNumeric)
admin.site.register(ReadingText)
admin.site.register(ReductionByTime)
admin.site.register(ReductionByDelta)
admin.site.register(ReductionByDuplicates)
admin.site.register(FilterDelta)
admin.site.register(InputFiltering)
admin.site.register(TagNumeric)
admin.site.register(TagDiscrete)
admin.site.register(TagText)
admin.site.register(TagNumericLimits)
admin.site.register(TagStrictValueNumeric)
admin.site.register(TagStrictValueDiscrete)
admin.site.register(TagStrictValueText)
admin.site.register(ValueNumeric)
admin.site.register(ValueDiscrete)
admin.site.register(ValueText)
admin.site.register(ViewSet)
admin.site.register(ReductionTimeBased)
