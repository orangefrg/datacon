from django.db import models
from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
import uuid
from datetime import datetime

MAXIMUM_VALUES_NUMBER = 500


class DataSource(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Идентификатор")
    name = models.CharField(max_length=100, verbose_name="Название")
    maintainer = models.ForeignKey(User, verbose_name="Пользователь", on_delete=models.CASCADE, default=AnonymousUser)
    quota = models.IntegerField(null=True, default=500, verbose_name="Квота")
    active = models.BooleanField(default=True, verbose_name="Активность")
    class Meta:
        ordering = ['name']
        verbose_name = "Источник данных"
        verbose_name_plural = "Источники данных"

    def __str__(self):
        return "{} - {} ({} {}) [{}]".format(self.name, self.uid, self.maintainer.first_name,
                                        self.maintainer.last_name, "ACT" if self.active else "OFF")


class Error(models.Model):
    error = models.TextField(unique=True, verbose_name="Текст ошибки")
    description = models.TextField(null=True, blank=True, default=None, verbose_name="Описание ошибки")
    class Meta:
        ordering = ['error']
        verbose_name = "Ошибка"
        verbose_name_plural = "Ошибки"
    def __str__(self):
        return self.error


class InputFiltering(models.Model):
    deadband = models.FloatField(null=True, blank=True, verbose_name="Интервал нечувствительности")
    minimum_delay = models.FloatField(null=True, blank=True, verbose_name="Минимальный интервал времени между данными")

    class Meta:
        verbose_name = "Фильтр входных данных"
        verbose_name_plural = "Фильтры входных данных"

    def __str__(self):
        ret = ""
        if self.deadband is not None:
            ret += " +/-{}".format(self.deadband)
        if self.minimum_delay is not None:
            ret += " time: >{} s".format(self.minimum_delay)
        return ret


class Tag(models.Model):
    data_source = models.ForeignKey(DataSource, on_delete=models.SET_NULL, null=True, verbose_name="Источник данных")
    name = models.CharField(max_length=255, verbose_name="Наименование")
    display_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Отображаемое имя")
    ignore_duplicates = models.BooleanField(default=True, verbose_name="Удалять дубликаты")

    class Meta:
        abstract = True
        unique_together = ("data_source", "name")
        ordering = ['name']

    def __str__(self):
        ret = self.name
        if self.display_name is None:
            ret += " ({})".format(self.display_name)
        return ret

    def _filter_new_value(self, value, timestamp_obtain, error):
        if self.ignore_duplicates:
            try:
                latest = self.values.filter(timestamp_obtain__lte=timestamp_obtain).latest()
                if latest.value == value and ((latest.error is None and error is None) or (latest.error.error == error)):
                    latest.save(force_update=True)
                    return False
                else:
                    return True
            except ObjectDoesNotExist:
                return True
        else:
            return True

    def add_value(self, value, error=None, timestamp_obtain=datetime.now(), time_to_obtain=0):
        need_to_add = self._filter_new_value(value, timestamp_obtain, error)
        if need_to_add:
            self.values.create(
                value=value,
                error=error,
                timestamp_obtain=timestamp_obtain,
                time_to_obtain=time_to_obtain
            )
        else:
            return True
    
    def get_latest_value(self, only_valid=True, by_date=None):
        try:
            kw = {}
            if only_valid:
                kw["error"] = None
            if by_date is not None:
                kw["timestamp_obtain__lte"] = by_date
            return [self.values.filter(**kw).latest()]
        except ObjectDoesNotExist:
            return []

    def get_range_of_values(self, date_start=None, date_end=None, only_valid=True, max_number=MAXIMUM_VALUES_NUMBER, bound_earlier=True):
        kw = {}
        vals = {}
        if max_number > MAXIMUM_VALUES_NUMBER:
            max_number = MAXIMUM_VALUES_NUMBER
        if only_valid:
            kw["error"] = None
        if date_end is not None:
            kw["timestamp_obtain__lte"] = date_end
        if date_start is not None:
            kw["timestamp_obtain__gte"] = date_start
        try:
            vals = self.values.filter(**kw).order_by("-timestamp_obtain")[:max_number]
        except ObjectDoesNotExist:
            if bound_earlier and date_start is not None:
                del kw["timestamp_obtain__gte"]
                try:
                    vals = self.values.filter(**kw).latest()
                except ObjectDoesNotExist:
                    return []
        return vals


class TagNumeric(Tag):
    units = models.CharField(max_length=40, null=True, blank=True, verbose_name="Единицы измерения")
    input_filter = models.ForeignKey(InputFiltering, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Фильтр входных данных")
    tag_type = "Numeric"
    def _filter_new_value(self, value, timestamp_obtain, error):
        try:
            latest = self.values.filter(timestamp_obtain__lte=timestamp_obtain).latest()
            if not super()._filter_new_value(value, timestamp_obtain, error):
                return False
            if self.input_filter is not None:
                if error is not None:
                    if latest.error is None or latest.error.error != error:
                        return True
                if self.input_filter.deadband is not None and latest.value is not None:
                    if abs(latest.value - value) <= self.input_filter.deadband:
                        latest.save(force_update=True)
                        return False
                if self.input_filter.minimum_delay is not None:
                    if abs((timestamp_obtain - latest.timestamp_obtain).total_seconds()) <= self.input_filter.minimum_delay:
                        latest.save(force_update=True)
                        return False
        except ObjectDoesNotExist:
            return True
        return True
        

    class Meta:
        verbose_name = "Тэг (численный)"
        verbose_name_plural = "Тэги (численные)"


class TagDiscrete(Tag):
    tag_type = "Discrete"
    class Meta:
        verbose_name = "Тэг (дискретный)"
        verbose_name_plural = "Тэги (дискретные)"


class TagText(Tag):
    tag_type = "Text"
    class Meta:
        verbose_name = "Тэг (текстовый)"
        verbose_name_plural = "Тэги (текстовые)"


class TagNumericLimits(models.Model):
    controlled_tags = models.ManyToManyField(TagNumeric, verbose_name="Контролируемые тэги", related_name="limits")
    critical_upper_boundary = models.ForeignKey(TagNumeric, null=True, blank=True, on_delete=models.SET_NULL,
                                                related_name="critical_upper_of", verbose_name="Верхняя аварийная граница")
    upper_boundary = models.ForeignKey(TagNumeric, null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name="upper_of", verbose_name="Верхняя нормативная граница")
    lower_boundary = models.ForeignKey(TagNumeric, null=True, blank=True, on_delete=models.SET_NULL,
                                       related_name="lower_of", verbose_name="Нижняя нормативная граница")
    critical_lower_boundary = models.ForeignKey(TagNumeric, null=True, blank=True, on_delete=models.SET_NULL,
                                                related_name="critical_lower_of", verbose_name="Нижняя аварийная граница")

    class Meta:
        verbose_name = "Ограничения тэга"
        verbose_name_plural = "Ограничения тэгов"

    def get_boundaries(self, by_date=None):
        ret = {}
        for t in [(self.critical_upper_boundary, "critical_upper"),
                  (self.upper_boundary, "upper"),
                  (self.lower_boundary, "lower"),
                  (self.critical_lower_boundary, "critical_lower")]:
            if t is not None:
                latest = t[0].get_latest_value(by_date=by_date)
                if len(latest) > 0:
                    ret[t[1]] = latest[0].value
        return ret

    def __str__(self):
        ret = ""
        for t in [(self.critical_upper_boundary, "CU"),
                  (self.upper_boundary, "U"),
                  (self.lower_boundary, "L"),
                  (self.critical_lower_boundary, "CL")]:
            if t is not None:
                latest = t[0].get_latest_value(by_date=by_date)
                if len(latest) > 0:
                    ret += " {}={},".format(t[1], latest[0].value)
        if ret=="":
            ret = "No data"
        return ret


class TagStrictValue(models.Model):

    class Meta:
            abstract = True
    def get_value(self, by_date=None):
        return self.strict_tag.get_latest_value(by_date=by_date)

    def __str__(self):
        ret = self.get_value()
        if ret is None:
            ret = "No data"
        ret += " (tag: {})".format(self.strict_tag.name)
        return ret


class TagStrictValueNumeric(TagStrictValue):
    controlled_tags = models.ManyToManyField(TagNumeric, verbose_name="Контролируемые тэги", related_name="strict_values")
    strict_tag = models.ForeignKey(TagNumeric, on_delete=models.CASCADE, verbose_name="Тэг со значением", related_name="strict_tag_of")

    class Meta:
        verbose_name = "Строгое значение (численное)"
        verbose_name_plural = "Строгие значения (численные)"

class TagStrictValueDiscrete(TagStrictValue):
    controlled_tags = models.ManyToManyField(TagDiscrete, verbose_name="Контролируемые тэги", related_name="strict_values")
    strict_tag = models.ForeignKey(TagDiscrete, on_delete=models.CASCADE, verbose_name="Тэг со значением", related_name="strict_tag_of")

    class Meta:
        verbose_name = "Строгое значение (дискретное)"
        verbose_name_plural = "Строгие значения (дискретные)"

class TagStrictValueText(TagStrictValue):
    controlled_tags = models.ManyToManyField(TagText, verbose_name="Контролируемые тэги", related_name="strict_values")
    strict_tag = models.ForeignKey(TagText, on_delete=models.CASCADE, verbose_name="Тэг со значением", related_name="strict_tag_of")

    class Meta:
        verbose_name = "Строгое значение (текстовое)"
        verbose_name_plural = "Строгие значения (текстовые)"


class Value(models.Model):
    timestamp_obtain = models.DateTimeField(verbose_name="Время получения данных")
    timestamp_receive = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Время получения на сервере")
    timestamp_update = models.DateTimeField(auto_now=True, verbose_name="Время последнего обновления на сервере")
    time_to_obtain = models.FloatField(verbose_name="Время измерения")

    error = models.ForeignKey(Error, null=True, blank=True, on_delete=models.PROTECT, verbose_name="Ошибка")

    class Meta:
        abstract = True
        get_latest_by = ['timestamp_obtain', 'timestamp_update']

    def __str__(self):
        ret = self.tag.name
        if self.value is not None:
            ret += " = " + str(self.value)
            if hasattr(self.tag, "units") and self.tag.units is not None:
                ret += self.tag.units
        if self.error is not None:
            ret += " [ERROR]"
        return ret


class ValueNumeric(Value):
    tag = models.ForeignKey(TagNumeric, on_delete=models.CASCADE, verbose_name="Элемент данных", related_name="values")
    value = models.FloatField(null=True, blank=True, verbose_name="Значение")

    class Meta:
        verbose_name = "Значение (численное)"
        verbose_name_plural = "Значения (численные)"
        get_latest_by = ['timestamp_obtain', 'timestamp_update']


class ValueDiscrete(Value):
    tag = models.ForeignKey(TagDiscrete, on_delete=models.CASCADE, verbose_name="Элемент данных", related_name="values")
    value = models.NullBooleanField(null=True, blank=True, verbose_name="Значение")

    class Meta:
        verbose_name = "Значение (дискретное)"
        verbose_name_plural = "Значения (дискретные)"
        get_latest_by = ['timestamp_obtain', 'timestamp_update']


class ValueText(Value):
    tag = models.ForeignKey(TagText, on_delete=models.CASCADE, verbose_name="Элемент данных", related_name="values")
    value = models.TextField(null=True, blank=True, verbose_name="Значение")

    class Meta:
        verbose_name = "Значение (текстовое)"
        verbose_name_plural = "Значения (текстовые)"
        get_latest_by = ['timestamp_obtain', 'timestamp_update']


class ViewSet(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Идентификатор")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=200, verbose_name="Название")
    tags_numeric = models.ManyToManyField(TagNumeric, blank=True, verbose_name="Численные тэги", related_name="viewsets")
    tags_discrete = models.ManyToManyField(TagDiscrete, blank=True, verbose_name="Дискретные тэги", related_name="viewsets")
    tags_text = models.ManyToManyField(TagText, blank=True, verbose_name="Текстовые тэги", related_name="viewsets")

    class Meta:
        ordering = ['name']
        verbose_name = "Набор данных"
        verbose_name_plural = "Наборы данных"

    def tag_count(self):
        return self.tags_numeric.count() + self.tags_discrete.count() + self.tags_text.count()

    def tags(self):
        tags = []
        tags.extend(list(self.tags_numeric.all()))
        tags.extend(list(self.tags_discrete.all()))
        tags.extend(list(self.tags_text.all()))
        return tags

    def __str__(self):
        return "{} - {} ({} {}), {} тэгов".format(self.name, self.uid, self.user.first_name, self.user.last_name,
                                                  self.tag_count())


class ReductionTimeBased(models.Model):
    time_back_ago = models.FloatField(verbose_name="Возраст данных для редукции (дней)")
    minimum_timespan = models.FloatField(verbose_name="Минимальный интервал между данными (секунд)")

    class Meta:
        abstract = True

    def __str__(self):
        return "T:{} d, D:{} s".format(self.time_back_ago, self.minimum_timespan)


class ReductionTimeBasedNumeric(ReductionTimeBased):
    tags = models.ManyToManyField(TagNumeric, verbose_name="Тэги", related_name="timebased_reduced_by")

    class Meta:
        verbose_name = "Очистка базы по времени (численные тэги)"
        verbose_name_plural = "Правила очистки базы по времени (численные тэги)"


class ReductionTimeBasedDiscrete(ReductionTimeBased):
    tags = models.ManyToManyField(TagDiscrete, verbose_name="Тэги", related_name="timebased_reduced_by")

    class Meta:
        verbose_name = "Очистка базы по времени (дискретные тэги)"
        verbose_name_plural = "Правила очистки базы по времени (дискретные тэги)"


class ReductionTimeBasedText(ReductionTimeBased):
    tags = models.ManyToManyField(TagText, verbose_name="Тэги", related_name="timebased_reduced_by")

    class Meta:
        verbose_name = "Очистка базы по времени (текстовые тэги)"
        verbose_name_plural = "Правила очистки базы по времени (текстовые тэги)"

