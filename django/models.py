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


class FilterDelta(models.Model):
    delta_value = models.FloatField(verbose_name="Интервал нечувствительности")
    def __str__(self):
        return "+/- {}".format(self.delta_value)
    class Meta:
        ordering = ['delta_value']
        verbose_name = "Интервал нечувствительности"
        verbose_name_plural = "Интервалы нечувствительности"


class DataTag(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, verbose_name="Источник")
    name = models.CharField(max_length=255, verbose_name="Название")
    units = models.CharField(max_length=40, verbose_name="Единицы измерения", blank=True, default="")
    display_name = models.CharField(max_length=200, verbose_name="Отображаемое название", blank=True, default="")
    ignore_duplicates = models.BooleanField(default=False, verbose_name="Игнорировать повторяющиеся значения")
    filter_delta = models.ForeignKey(FilterDelta, blank=True, null=True, verbose_name="Интервал нечувствительности", on_delete=models.SET_NULL)
    class Meta:
        ordering = ['name']
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
    
    def get_full_name(self):
        return "{}.{}".format(self.source.name, self.name)

    def __str__(self):
        ret = ""
        if len(self.display_name) > 0:
            ret = "{} ({})".format(self.display_name, self.get_full_name())
        else:
            ret = self.get_full_name()
        if self.ignore_duplicates:
            ret += " (no dup)"
        if self.filter_delta is not None:
            ret += " (deadband {})".format(self.filter_delta.delta_value)
        return ret

    def latest_reading(self, only_valid=True):
        kw = {
            "tag": self
        }
        if only_valid:
            kw["error"] = None
        r_all = []
        try:
            r_all.append(ReadingNumeric.objects.filter(**kw).latest("timestamp_packet"))
        except ObjectDoesNotExist:
            pass
        try:
            r_all.append(ReadingDiscrete.objects.filter(**kw).latest("timestamp_packet"))
        except ObjectDoesNotExist:
            pass
        try:
            r_all.append(ReadingText.objects.filter(**kw).latest("timestamp_packet"))
        except ObjectDoesNotExist:
            pass
        r_all = sorted(r_all, key=lambda k: k.timestamp_packet, reverse=True)
        if len(r_all) == 0:
            return None
        else:
            return r_all[0]
        
    def latest_n_readings(self, number=30, only_valid=True):
        kw = {
            "tag": self
        }
        if only_valid:
            kw["error"] = None
        r_all = list(ReadingNumeric.objects.filter(**kw).order_by("-timestamp_packet")[:number])
        r_all.extend(list(ReadingDiscrete.objects.filter(**kw).order_by("-timestamp_packet")[:number]))
        r_all.extend(list(ReadingText.objects.filter(**kw).order_by("-timestamp_packet")[:number]))
        r_sorted = sorted(r_all, key=lambda k: k.timestamp_packet, reverse=True)[:number]
        return r_sorted

    def range_of_readings(self, date_start, date_end=None, max_number=None, only_valid=True, bound_earlier=True, bound_later=False):
        kw = {
            "tag": self,
            "timestamp_packet__gte": date_start
        }
        if date_end is not None:
            kw["timestamp_packet__lte"] = date_end
        elif bound_later:
            date_end = datetime.now()
        if only_valid:
            kw["error"] = None
        r_all = list(ReadingNumeric.objects.filter(**kw))
        r_all.extend(list(ReadingDiscrete.objects.filter(**kw)))
        r_all.extend(list(ReadingText.objects.filter(**kw)))
        if max_number is None:
            max_number = 100
        r_sorted = sorted(r_all, key=lambda k: k.timestamp_packet, reverse=True)[:max_number]
        if len(r_all)==0:
            if bound_later:
                kw_later = {
                    "tag": self,
                    "timestamp_packet__gte": date_end
                }
                r_later = []
                try:
                    r_later.append(list(ReadingNumeric.objects.filter(**kw_later).order_by("timestamp_packet"))[0])
                except IndexError:
                    pass
                try:
                    r_later.append(list(ReadingDiscrete.objects.filter(**kw_later).order_by("timestamp_packet"))[0])
                except IndexError:
                    pass
                try:
                    r_later.append(list(ReadingText.objects.filter(**kw_later).order_by("timestamp_packet"))[0])
                except IndexError:
                    pass
                if len(r_later) > 0:
                    r_sorted.append(sorted(r_later, key=lambda k: k.timestamp_packet)[0])
            if bound_earlier:
                kw_earlier = {
                    "tag": self,
                    "timestamp_packet__lte": date_start
                }
                r_earlier = []
                try:
                    r_earlier.append(list(ReadingNumeric.objects.filter(**kw_earlier).order_by("-timestamp_packet"))[0])
                except IndexError:
                    pass
                try:
                    r_earlier.append(list(ReadingDiscrete.objects.filter(**kw_earlier).order_by("-timestamp_packet"))[0])
                except IndexError:
                    pass
                try:
                    r_earlier.append(list(ReadingText.objects.filter(**kw_earlier).order_by("-timestamp_packet"))[0])
                except IndexError:
                    pass
                if len(r_earlier) > 0:
                    r_sorted.append(sorted(r_earlier, key=lambda k: k.timestamp_packet, reverse=True)[0])
        return r_sorted


class Error(models.Model):
    error = models.TextField(unique=True, verbose_name="Текст ошибки")
    description = models.TextField(null=True, blank=True, default=None, verbose_name="Описание ошибки")
    class Meta:
        ordering = ['error']
        verbose_name = "Ошибка"
        verbose_name_plural = "Ошибки"
    def __str__(self):
        return self.error


class Reading(models.Model):
    tag = models.ForeignKey(DataTag, on_delete=models.CASCADE, verbose_name="Тэг")
    timestamp_packet = models.DateTimeField(verbose_name="Метка времени в пакете")
    timestamp_receive = models.DateTimeField(auto_now_add=True, verbose_name="Метка времени получения")
    time_to_obtain = models.FloatField(verbose_name="Время измерения")
    error = models.ForeignKey(Error, null=True, blank=True, verbose_name="Ошибка", on_delete=models.SET_NULL)
    class Meta:
        abstract = True
    def __str__(self):
        return "{} = {} ({})".format(self.tag.get_full_name(), self.reading, self.timestamp_packet)
    def timestamp_packet_as_string(self):
        return self.timestamp_packet.isoformat()
    def timestamp_receive_as_string(self):
        return self.timestamp_receive.isoformat()

class ReadingNumeric(Reading):
    reading = models.FloatField(null=True)
    class Meta:
        ordering = ['timestamp_receive']
        verbose_name = "Численное значение"
        verbose_name_plural = "Численные значения"

class ReadingDiscrete(Reading):
    reading = models.BooleanField(default=False)
    class Meta:
        ordering = ['timestamp_receive']
        verbose_name = "Дискретное значение"
        verbose_name_plural = "Дискретные значения"

class ReadingText(Reading):
    reading = models.TextField(null=True)
    class Meta:
        ordering = ['timestamp_receive']
        verbose_name = "Текстовое значение"
        verbose_name_plural = "Текстовые значения"

class AlertValues(models.Model):
    parameter = models.OneToOneField(DataTag, on_delete=models.CASCADE, verbose_name="Параметр", related_name="alert_values")
    upper_boundary = models.ForeignKey(DataTag, null=True, blank=True, default=None, on_delete=models.CASCADE,
                                       verbose_name="Верхняя нормативная граница", related_name="upper_boundary_of")
    lower_boundary = models.ForeignKey(DataTag, null=True, blank=True, default=None, on_delete=models.CASCADE,
                                       verbose_name="Нижняя нормативная граница", related_name="lower_boundary_of")
    critical_upper_boundary = models.ForeignKey(DataTag, null=True, blank=True, default=None, on_delete=models.CASCADE,
                                                verbose_name="Верхняя аварийная граница", related_name="critical_upper_boundary_of")
    critical_lower_boundary = models.ForeignKey(DataTag, null=True, blank=True, default=None, on_delete=models.CASCADE,
                                                verbose_name="Нижняя аварийная граница", related_name="critical_lower_boundary_of")
    strict_equal_value = models.ForeignKey(DataTag, null=True, blank=True, default=None, on_delete=models.CASCADE,
                                     verbose_name="Строгое нормативное значение", related_name="strict_equal_value_of")

    class Meta:
        ordering = ['parameter']
        verbose_name = "Ограничения параметра"
        verbose_name_plural = "Ограничения параметров"
    def __str__(self):
        out_str = self.parameter.get_full_name()
        out_limits = []
        if self.critical_lower_boundary is not None:
            out_limits.append("CritLow")
        if self.lower_boundary is not None:
            out_limits.append("Low")
        if self.strict_equal_value is not None:
            out_limits.append("Strict")
        if self.upper_boundary is not None:
            out_limits.append("High")
        if self.critical_upper_boundary is not None:
            out_limits.append("CritHigh")
        if len(out_limits) > 0:
            out_str += " ({})".format(", ".join(out_limits))
        else:
            out_str += " (no limits)"
        return out_str

class DataSet(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Идентификатор")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=200, verbose_name="Название")
    tags = models.ManyToManyField(DataTag, verbose_name="Тэги")
    class Meta:
        ordering = ['name']
        verbose_name = "Набор данных"
        verbose_name_plural = "Наборы данных"
    def __str__(self):
        return "{} - {} ({} {}), {} тэгов".format(self.name, self.uid, self.user.first_name, self.user.last_name,
                                                  self.tags.count())

class ReductionByTime(models.Model):
    tags = models.ManyToManyField(DataTag, verbose_name="Тэги")
    time_back_ago = models.FloatField(verbose_name="Возраст данных для редукции")
    minimum_timespan = models.FloatField(verbose_name="Минимальный интервал между данными")
    class Meta:
        verbose_name = "Редукция по времени"
        verbose_name_plural = "Правила редукции по времени"

class ReductionByDelta(models.Model):
    tags = models.ManyToManyField(DataTag, verbose_name="Тэги")
    time_back_ago = models.FloatField(verbose_name="Возраст данных для редукции")
    minimum_delta = models.FloatField(verbose_name="Минимальная разница в значении параметра")
    class Meta:
        verbose_name = "Редукция по пороговому значению"
        verbose_name_plural = "Правила редукции по пороговому значению"

class ReductionByDuplicates(models.Model):
    tags = models.ManyToManyField(DataTag, verbose_name="Тэги")
    class Meta:
        verbose_name = "Редукция по дубликатам"
        verbose_name_plural = "Правила редукции по дубликатам"

# Refactored models #

class InputFiltering(models.Model):
    deadband = models.FloatField(null=True, blank=True, verbose_name="Интервал нечувствительности")
    minimum_delay = models.FloatField(null=True, blank=True, verbose_name="Минимальный интервал времени между данными")

    class Meta:
        verbose_name = "Фильтр входных данных"
        verbose_name_plural = "Фильтры входных данных"


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
            latest = self.values.filter(timestamp_obtain__lte=timestamp_obtain).latest()
            if latest.value == value and ((latest.error is None and error is None) or (latest.error.error == error)):
                latest.save()
                return False
        return True

    def add_value(self, value, error=None, timestamp_obtain=datetime.now(), time_to_obtain=0):
        is_valid = self._filter_new_value(value, timestamp_obtain, error)
        if is_valid:
            self.values.create(
                value=value,
                error=error,
                timestamp_obtain=timestamp_obtain,
                time_to_obtain=time_to_obtain
            )
        return True
    
    def get_latest_value(self, only_valid=True, by_date=None):
        try:
            kw = {}
            if only_valid:
                kw["error"] = None
            if by_date is not None:
                kw["timestamp_obtain__lte"] = by_date
            return self.values.filter(**kw).latest()
        except ObjectDoesNotExist:
            return None

    def get_range_of_values(self, date_start=None, date_end=None, only_valid=True, max_number=MAXIMUM_VALUES_NUMBER, bound_earlier=True):
        kw = {}
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
                    return None
        return vals


class TagNumeric(Tag):
    units = models.CharField(max_length=40, null=True, blank=True, verbose_name="Единицы измерения")
    input_filter = models.ForeignKey(InputFiltering, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Фильтр входных данных")
    tag_type = "Numeric"
    def _filter_new_value(self, value, timestamp_obtain, error):
        latest = self.values.filter(timestamp_obtain__lte=timestamp_obtain).latest()
        if not super._filter_new_value(value, timestamp_obtain, error):
            return False
        if self.input_filter is not None:
            try:
                if error is not None:
                    if latest.error is None or latest.error.error != error:
                        return True
                if self.input_filter.deadband is not None:
                    if abs(latest.value - value) <= self.input_filter.deadband:
                        latest.save()
                        return False
                if self.input_filter.minimum_delay is not None:
                    if abs((timestamp_obtain - latest.timestamp_obtain).total_seconds()) <= self.input_filter.minimum_delay:
                        latest.save()
                        return False
            finally:
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
                ret[t[1]] = t[0].get_latest_value(by_date=by_date)
        return ret

    def __str__(self):
        ret = ""
        for t in [(self.critical_upper_boundary, "CU"),
                  (self.upper_boundary, "U"),
                  (self.lower_boundary, "L"),
                  (self.critical_lower_boundary, "CL")]:
            if t is not None:
                ret += " {}={},".format(t[1], t[0].get_latest_value())
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

class TagStrictValueDiscrete(TagStrictValue):
    controlled_tags = models.ManyToManyField(TagDiscrete, verbose_name="Контролируемые тэги", related_name="strict_values")
    strict_tag = models.ForeignKey(TagDiscrete, on_delete=models.CASCADE, verbose_name="Тэг со значением", related_name="strict_tag_of")

class TagStrictValueText(TagStrictValue):
    controlled_tags = models.ManyToManyField(TagText, verbose_name="Контролируемые тэги", related_name="strict_values")
    strict_tag = models.ForeignKey(TagText, on_delete=models.CASCADE, verbose_name="Тэг со значением", related_name="strict_tag_of")


class Value(models.Model):
    timestamp_obtain = models.DateTimeField(verbose_name="Время получения данных")
    timestamp_receive = models.DateTimeField(auto_now_add=True, editable=False, verbose_name="Время получения на сервере")
    timestamp_update = models.DateTimeField(auto_now=True, verbose_name="Время последнего обновления на сервере")
    time_to_obtain = models.FloatField(verbose_name="Время измерения")

    error = models.ForeignKey(null=True, blank=True, on_delete=models.PROTECT, verbose_name="Ошибка")

    class Meta:
        abstract = True
        get_latest_by = ['timestamp_obtain', 'timestamp_update']

    def __str__(self):
        ret = self.tag.name
        if self.value is not None:
            ret += " = " + self.value
            if hasattr(self.tag, "units") and self.tag.units is not None:
                ret += self.tag.units
        if self.error is not None:
            ret += " [ERROR]"


class ValueNumeric(Value):
    tag = models.ForeignKey(TagNumeric, on_delete=models.CASCADE, verbose_name="Элемент данных", related_name="values")
    value = models.FloatField(null=True, blank=True, verbose_name="Значение")

    class Meta:
        verbose_name = "Значение (численное)"
        verbose_name_plural = "Значения (численные)"


class ValueDiscrete(Value):
    tag = models.ForeignKey(TagDiscrete, on_delete=models.CASCADE, verbose_name="Элемент данных", related_name="values")
    value = models.BooleanField(null=True, blank=True, verbose_name="Значение")

    class Meta:
        verbose_name = "Значение (дискретное)"
        verbose_name_plural = "Значения (дискретные)"


class ValueText(Value):
    tag = models.ForeignKey(TagText, on_delete=models.CASCADE, verbose_name="Элемент данных", related_name="values")
    value = models.TextField(null=True, blank=True, verbose_name="Значение")

    class Meta:
        verbose_name = "Значение (текстовое)"
        verbose_name_plural = "Значения (текстовые)"


class ViewSet(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Идентификатор")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    name = models.CharField(max_length=200, verbose_name="Название")
    tags_numeric = models.ManyToManyField(TagNumeric, verbose_name="Численные тэги", related_name="viewsets")
    tags_discrete = models.ManyToManyField(TagDiscrete, verbose_name="Дискретные тэги", related_name="viewsets")
    tags_text = models.ManyToManyField(TagDiscrete, verbose_name="Текстовые тэги", related_name="viewsets")

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


class ReductionNumeric(models.Model):
    tags = models.ManyToManyField(TagNumeric, verbose_name="Тэги", related_name="numeric_reduced_by")
    time_back_ago = models.FloatField(verbose_name="Возраст данных для редукции")
    minimum_delta = models.FloatField(verbose_name="Минимальная разница в значении параметра")

    class Meta:
        verbose_name = "Очистка базы по пороговому значению"
        verbose_name_plural = "Правила очистки базы по пороговому значению"

    def __str__(self):
        return "T:{} s, D:{}".format(self.time_back_ago, self.minimum_delta)


class ReductionTimeBased(models.Model):
    tags = models.ManyToManyField(DataTag, verbose_name="Тэги", related_name="time_reduced_by")
    time_back_ago = models.FloatField(verbose_name="Возраст данных для редукции")
    minimum_timespan = models.FloatField(verbose_name="Минимальный интервал между данными")

    class Meta:
        verbose_name = "Очистка базы по времени"
        verbose_name_plural = "Правила очистки базы по времени"

    def __str__(self):
        return "T:{} s, D:{} s".format(self.time_back_ago, self.minimum_timespan)

