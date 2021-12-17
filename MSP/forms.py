from django import forms
from .models import Lesson, Hometask, Exam, Settings, Time, Subject, Plan

from datetime import datetime
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

forms.fields.Field.default_error_messages = {'required': '', }
weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
WEEKDAY_CHOICES = [(x, weekdays[x]) for x in range(7)]


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ('title', 'weekday', 'time', 'start_time', 'end_time', 'teacher', 'classroom', 'link', 'type')
        labels = {'title': "Название", 'weekday': 'День недели', 'date': "Дата", 'time': 'Номер занятия',
                  'start_time': "Время начала", 'end_time': 'Время окончания', 'teacher': "Преподаватель",
                  'classroom': "Кабинет", 'link': "Ссылка", 'type': "Тип занятия"}
        widgets = {'weekday': forms.Select(choices=WEEKDAY_CHOICES)}


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = (
        'select_subject', 'title', 'time', 'start_time', 'end_time', 'teacher', 'classroom', 'link', 'notes', 'type')
        labels = {'select_subject': 'Предмет', 'title': "Название", 'time': 'Номер занятия',
                  'start_time': "Время начала", 'end_time': 'Время окончания', 'teacher': "Преподаватель",
                  'classroom': "Кабинет", 'link': "Ссылка", 'notes': "Заметки", 'type': "Тип занятия"}
        

        def __init__(self, *args, **kwargs):
            super(LessonForm, self).__init__(*args, **kwargs)
            self.user = kwargs.pop('user', None)
            self.fields['select_subject'].queryset = self.fields['select_subject'].queryset.filter(owner=self.user)


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ('start_date', 'end_date')
        labels = {'start_date': "Начало семестра", 'end_date': 'Конец семестра', 'exams_date':'Дата начала сессии'}
        widgets = {'start_date': forms.SelectDateWidget(years=range(2020, 2030)), 'end_date': forms.SelectDateWidget(),'exams_date': forms.SelectDateWidget()}


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = ('repeating_weeks', 'first_lesson_start', 'lesson_length', 'break_length', 'max_lessons')
        labels = {'repeating_weeks': 'Число повторяющихся недель', 'first_lesson_start': "Время начала занятий",
                  'lesson_length': "Длина занятия", 'break_length': "Длина перемены",
                  'max_lessons': "Максимальное число занятий"}
        widgets = {'repeating_weeks':forms.NumberInput(attrs={'style':'width:50px'}), 'first_lesson_start':forms.TimeInput(attrs={'style':'width:100px'}), 'lesson_length':forms.NumberInput(attrs={'style':'width:50px'}), 'break_length':forms.NumberInput(attrs={'style':'width:50px'}),'max_lessons':forms.NumberInput(attrs={'style':'width:50px'})}


class TimeForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ('start_time', 'end_time')
        labels = {'start_time': '', 'end_time': ''}


class TaskForm(forms.ModelForm):
    class Meta:
        model = Hometask
        fields = ('lesson', 'hometask', 'notes')
        labels = {'lesson': 'Занятие', 'hometask': 'Задание', 'notes': 'Заметки'}
        

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        today = datetime.now().date()
        self.user = kwargs.pop('user', None)
        self.fields['lesson'].queryset = self.fields['lesson'].queryset.filter(date__gte=today,owner=self.user).order_by('date')

class TaskMobileForm(forms.ModelForm):
    class Meta:
        model = Hometask
        fields = ('lesson', 'hometask', 'notes')
        labels = {'lesson': 'Занятие', 'hometask': 'Задание', 'notes': 'Заметки'}
        widgets = {'notes': forms.Textarea(attrs={'style':'width:1000px;height:100;font-size:50px;'}),'lesson':forms.Select(attrs={'style':'width:1000px;height:50px;font-size:50px;'}),'hometask':forms.TextInput(attrs={'style':'width:1000px;height:50px;font-size:50px;'}) }

    def __init__(self, *args, **kwargs):
        super(TaskMobileForm, self).__init__(*args, **kwargs)
        today = datetime.now().date()
        self.user = kwargs.pop('user', None)
        self.fields['lesson'].queryset = self.fields['lesson'].queryset.filter(date__gte=today,owner=self.user).order_by('date')


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ('lesson', 'type', 'topic', 'time', 'start_time', 'notes')
        labels = {'lesson': 'Занятие', 'type': 'Вид работы', 'topic': 'Тема', 'time': 'Номер занятия',
                  'start_time': "Время начала", 'notes': 'Заметки'}
        

    def __init__(self, *args, **kwargs):
        super(ExamForm, self).__init__(*args, **kwargs)
        today = datetime.now().date()
        self.user = kwargs.pop('user', None)
        self.fields['lesson'].queryset = self.fields['lesson'].queryset.filter(date__gte=today,owner=self.user).order_by('date')


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ('name', 'type', 'start_time', 'end_time', 'place', 'notes')
        labels = {'name': "Название", 'start_time': "Время начала", 'end_time': 'Время окончания', 'notes': "Заметки",
                  'type': "Вид мероприятия", 'place': 'Место'}
        


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False)
    first_name.label="Имя"
    email=forms.CharField(max_length=100, required=False)
    email.label = "Эл.почта"
    class Meta:
        model = User
        fields = ('username', 'first_name','email', 'password1', 'password2')


class LogInForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')
        labels = {'username': "Логин"}
