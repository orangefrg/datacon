from django.contrib import admin

from .models import DataSource, Error, TagNumeric, TagDiscrete, TagText
from .models import InputFiltering, TagNumericLimits, TagStrictValueNumeric, TagStrictValueDiscrete, TagStrictValueText
from .models import ValueNumeric, ValueDiscrete, ValueText, ViewSet, ReductionTimeBasedNumeric, ReductionTimeBasedDiscrete, ReductionTimeBasedText

admin.site.register(DataSource)
admin.site.register(Error)
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
admin.site.register(ReductionTimeBasedNumeric)
admin.site.register(ReductionTimeBasedDiscrete)
admin.site.register(ReductionTimeBasedText)
