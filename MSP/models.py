from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta, time, date, datetime
from django.contrib.auth.models import User
from django.db import models
from osm_field.fields import OSMField, LatitudeField, LongitudeField
from jsonfield import JSONField
import copy

weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
WEEKDAY_CHOICES = [(x, weekdays[x]) for x in range(7)]


class Day(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now, blank=True)
    weekday = models.IntegerField(default=0)
    week = models.IntegerField(default=0)

    def __str__(self):
        return str(self.date)

class Holiday(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    start_date = models.DateField(default=datetime.now().strftime("%Y-%m-%d"))
    end_date = models.DateField(default=datetime.now().strftime("%Y-%m-%d"))

    def __str__(self):
        return str(f'{self.start_date}-{self.end_date}')

class Settings(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True,on_delete=models.CASCADE)
    repeating_weeks = models.IntegerField(default=1)
    first_lesson_start = models.TimeField(default=time(9, 00))
    lesson_length = models.IntegerField(default=95)
    break_length = models.IntegerField(default=15)
    max_lessons = models.IntegerField(default=6)
    theme = models.CharField(max_length=7, default='#FF81F2')
    sub_color = models.CharField(max_length=7, default='#FFAFFC')
    start_date = models.DateField(default=datetime.now().strftime("%Y-%m-%d"))
    end_date = models.DateField(default=datetime.now().strftime("%Y-%m-%d"))
    exams_date=models.DateField(null=True, blank=True)
    homepage=models.CharField(default='timetable',max_length=50)
    university=models.CharField(default='НГУ',max_length=200)
    holidays=models.ManyToManyField(Holiday,blank=True)

    def __str__(self):
        return str(f'{self.owner}_config')


class Time(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    number = models.IntegerField(default=0)
    start_time = models.TimeField(default=timezone.now, blank=True)
    end_time = models.TimeField(default=timezone.now, blank=True)

    def __str__(self):
        return str(self.number)


class Image(models.Model):
    image = models.FileField(blank=True, null=True)
    path = models.CharField(max_length=200, blank=True, null=True)


class AbstractClass(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True, null=True)
    title_short = models.CharField(max_length=200, blank=True, null=True)
    teacher = models.CharField(max_length=200, default='', blank=True)
    teachershort = models.CharField(max_length=200, default='', blank=True)
    link = models.URLField(blank=True, null=True)
    color = models.CharField(max_length=200, default='#FF81F3')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, default=0)
    time = models.IntegerField(blank=True, null=True)
    start_time = models.TimeField(null=True, blank=True,default=None)
    end_time = models.TimeField(null=True, blank=True,default=None)
    image = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, default='', blank=True)
    classroom = models.CharField(max_length=200, default='', blank=True)

    class Meta:
        abstract = True


class Subject(AbstractClass):
    weeks = models.CharField(max_length=20, default='12')

    def clone(self):
        clone = copy.copy(self)
        clone.pk = None
        clone.is_sample = None
        clone.save()
        return clone

    def __str__(self):
        if self.title_short:
             name = self.title_short
        else:
            name=self.title
        if len(Subject.objects.filter(title=self.title)) > 1:
            if self.type:
                name += '- ' + self.type
                if len(Subject.objects.filter(title=self.title, type=self.type)) > 1:
                    name += '-' + weekdays[self.weekday].lower()
                    if len(Subject.objects.filter(title=self.title, type=self.type, weekday=self.weekday,
                                                  owner=self.owner)) > 1:
                        name += '-' + f'{self.start_time.hour}:{self.start_time.minute}'
            else:
                name += '-' + weekdays[self.weekday].lower()
                if len(Subject.objects.filter(title=self.title, weekday=self.weekday, owner=self.owner)) > 1:
                    name += '-' + f'{self.start_time.hour}:{self.start_time.minute}'
        return name


class Lesson(AbstractClass):
    select_subject = models.ForeignKey(Subject, on_delete=models.CASCADE, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.title) + ' (' + str(self.date) + ')'

    def add(self):
        self.save()


class Hometask(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    weekday = models.IntegerField(null=True, blank=True)
    hometask = models.CharField(max_length=200, blank=True, null=True)
    done = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    select_subject = models.ForeignKey(Subject, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return str(self.hometask)


class Exam(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    topic = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(null=True, blank=True)
    select_subject = models.ForeignKey(Subject, on_delete=models.CASCADE, blank=True, null=True)
    weekday = models.IntegerField(null=True, blank=True)
    examination = models.BooleanField(default=False)
    type = models.CharField(max_length=200, blank=True, null=True)
    time = models.IntegerField(blank=True, null=True)
    start_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        name = ''
        if self.select_subject:
            name = self.select_subject.title
        if self.type:
            name += ' ' + self.type
        if self.topic:
            name += ' ' + self.topic
        return name


class Plan(models.Model):
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=True, default='')
    notes = models.TextField(blank=True, null=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    weekday = models.IntegerField(null=True, blank=True)
    type = models.CharField(max_length=200, blank=True, null=True, default='')
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    place = models.CharField(max_length=500, blank=True, default='')
    location=OSMField(null=True)
    location_lat=LatitudeField(null=True)
    location_lon=LongitudeField(null=True)
    color = models.CharField(max_length=200, default='#FF81F3')

    def __str__(self):
        name = self.name
        if self.type:
            name += ' ' + self.type
        return name



