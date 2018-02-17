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
        return "{} ({} {}) [{}]".format(self.name, self.maintainer.first_name,
                                        self.maintainer.last_name, "ACT" if self.active else "OFF")

class DataTag(models.Model):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, verbose_name="Источник")
    name = models.CharField(max_length=255, verbose_name="Название")
    units = models.CharField(max_length=40, verbose_name="Единицы измерения", blank=True)
    class Meta:
        ordering = ['name']
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"
    
    def get_full_name(self):
        return "{}.{}".format(self.source.name, self.name)

    def __str__(self):
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
    error = models.ForeignKey(Error, null=True, verbose_name="Ошибка", on_delete=models.SET_NULL)
    class Meta:
        abstract = True
    def __str__(self):
        return "{} = {} ({})".format(self.tag.get_full_name(), self.reading, self.timestamp_packet)

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
        verbose_name = "Тесктовое значение"
        verbose_name_plural = "Текстовые значения"
