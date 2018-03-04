from django.db import models
from django.contrib.auth.models import User, AnonymousUser
import uuid

# Create your models here.

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

class DataTag(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, verbose_name="Источник")
    name = models.CharField(max_length=255, verbose_name="Название")
    units = models.CharField(max_length=40, verbose_name="Единицы измерения", blank=True, default="")
    display_name = models.CharField(max_length=200, verbose_name="Отображаемое название", blank=True, default="")
    class Meta:
        ordering = ['name']
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
    
    def get_full_name(self):
        return "{}.{}".format(self.source.name, self.name)

    def __str__(self):
        if len(self.display_name) > 0:
            return "{} ({})".format(self.display_name, self.get_full_name())
        return self.get_full_name()

class Error(models.Model):
    error = models.TextField(unique=True, verbose_name="Текст ошибки")
    description = models.TextField(null=True, blank=True, default=None)
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
                                     verbosk["time_back_ago"]e_name="Строгое нормативное значение", related_name="strict_equal_value_of")

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

# TODO: input filtering