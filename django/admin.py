from django.contrib import admin

from .models import DataSource, DataTag, Error, DataSet
from .models import ReadingDiscrete, ReadingNumeric, ReadingText

admin.site.register(DataSource)
admin.site.register(DataSet)
admin.site.register(DataTag)
admin.site.register(Error)
admin.site.register(ReadingDiscrete)
admin.site.register(ReadingNumeric)
admin.site.register(ReadingText)
