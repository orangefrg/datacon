from django.contrib import admin

from .models import DataSource, DataTag, Error
from .models import ReadingDiscrete, ReadingNumeric, ReadingText

admin.site.register(DataSource)
admin.site.register(DataTag)
admin.site.register(Error)
admin.site.register(ReadingDiscrete)
admin.site.register(ReadingNumeric)
admin.site.register(ReadingText)
