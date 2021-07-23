from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Lesson, Hometask, Exam, Settings, Time, Image, Day, Subject, Plan, Holiday
from .forms import SubjectForm, LessonForm, SettingsForm, TimeForm, TaskForm, SemesterForm, ExamForm, PlanForm,SignUpForm,LogInForm
from datetime import datetime, date, timedelta, time
from .syllables import syllables,shorten
from django.contrib.auth import login, authenticate
import random
from django.core.mail import send_mail
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django.shortcuts import HttpResponse
from django import template

weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
weekdays_short = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь",
          "Декабрь"]
colors = ["#FF67F9", "#CA34FF", "#179EFF", "#3DD8FA", "#00FEEF", "#00FEA3", "#80FE6C", "#D0FF4B", "#FAFF00",
          "#F8E438", "#FECC6C", "#FF8C4B", "#FE5A36", "#E4364B"]
sub_colors = ["#FFAFFC", "#E3BBFB", "#70C3FF", "#ADF0FF", "#ACFEF9", "#85FFD3", "#98FF88", "#E0FB93", "#FDFF8B",
                  "#FFF281", "#F9D591", "#FFA673", "#FF8165", "#F66D7D"]
palette = dict(zip(colors, sub_colors))
seconds_in_day=60*60*24
seconds_in_week=seconds_in_day*7

def shorten_title(t):
    if len(t) > 20:
        title = t.split(' ')
        for i in range(len(title)):
            title[i] = shorten(title[i])
        return ''.join(title)
    return t


def create_lessons(subject, lesson):
    if not lesson.teacher:
        lesson.teacher = subject.teacher
    if not lesson.teacher:
        lesson.teachershort = subject.teachershort
    if not lesson.teacher:
        lesson.classroom = subject.classroom
    if not lesson.teacher:
        lesson.image = subject.image
    if not lesson.teacher:
        lesson.title_short = subject.title_short
    lesson.weekday = subject.weekday
    lesson.color = subject.color
    return lesson

def password_reset(request):
    pass

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            Settings.objects.create(owner=user)
            settings=Settings.objects.get(owner=user)
            settings.start_date = datetime.strptime('01.09.2021', '%d.%m.%Y')
            settings.end_date = datetime.strptime('31.01.2022', '%d.%m.%Y')
            settings.save()
            return redirect('start')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def create_times(settings,user):
    first_delta = settings.first_lesson_start
    lesson_delta = timedelta(minutes=settings.lesson_length)
    break_delta = timedelta(minutes=settings.break_length)
    for i in range(settings.max_lessons):
        time = Time()
        time.number = i + 1
        time.start_time = (
                datetime.combine(date.today(), first_delta) + lesson_delta * i + break_delta * i).time()
        time.end_time = (datetime.combine(date.today(),
                                          first_delta) + lesson_delta * time.number + break_delta * i).time()
        time.owner = user
        time.save()

from icalendar import Calendar
import re
from django.contrib.staticfiles.storage import staticfiles_storage

def load_subjects_ics(link):
    with open(staticfiles_storage.url(f'calendars/{link}'), 'r', encoding='utf-8') as g:
        gcal = Calendar.from_ical(g.read())
        for component in gcal.walk():
            if component.name == 'VEVENT':
                subject = Subject()
                fullname = str(component.get('summary'))
                subject.type = str(re.findall('(\(.*?\))', fullname)[-1].strip('()'))
                subject.title = fullname.replace(f'({subject.type})', '').rstrip(' ')
                subject.start_time = component.decoded('dtstart').astimezone().strftime("%H:%M")
                subject.end_time = component.decoded('dtend').astimezone().strftime("%H:%M")
                subject.weekday = component.decoded('dtstart').weekday()
                subject.teacher = str(component.get('description')).replace('Преподаватель: ', '')
                subject.color = random.choice(colors)
                try:
                    subject.classroom = re.findall('[а-я]?\d+[а-я]?', str(component.get('location')))[0]
                except:
                    subject.classroom = str(component.get('location'))
import requests
from bs4 import BeautifulSoup
def load_subjects_html(group,user,settings):
    if len(Time.objects.filter(owner=user))==0:
        settings.first_lesson_start=datetime.strptime('09:00', '%H:%M').time()
        settings.lesson_length=95
        settings.break_length=15
        settings.max_lessons=7
        settings.repeating_weeks=2
        create_times(settings,user)
    timetable = requests.post(f'https://table.nsu.ru/group/{group}/').text
    soup = BeautifulSoup(timetable, 'html.parser')
    table = soup.find(class_='time-table')
    time = 0
    for row in table.find_all('tr'):
        columns = row.find_all('td')
        if columns:
            start_time = columns[0].string
            time += 1
            for i in range(1, len(columns)):
                if columns[i].find_all(class_='cell'):
                    subject = Subject()
                    subject.owner = user
                    subject.time=time
                    subject_time=Time.objects.get(owner=user,number=time)
                    subject.start_time = subject_time.start_time
                    subject.end_time = subject_time.end_time
                    subject.weekday = i - 1
                    subject.title = columns[i].find(class_='subject')['title']
                    try:
                        subject.classroom = columns[i].find(class_='room').find('a').string
                    except:
                        subject.classroom = columns[i].find(class_='room').string.strip(' \r')
                        if subject.classroom=='Ауд. Спортивный комплекс':
                            subject.classroom='спорт. комплекс'
                    if columns[i].find(class_='tutor'):
                        subject.teachershort = columns[i].find(class_='tutor').string
                        subject.teacher=subject.teachershort
                    subject.title_short=columns[i].find(class_='subject').string
                    subject.type = columns[i].find(class_=re.compile('type'))['title']
                    if subject.type == 'практическое занятие':
                        subject.type= 'практ. занятие'
                    weeks=columns[i].find(class_='week')
                    if weeks:
                        week=weeks.string
                        if week==' Нечетная':
                            subject.weeks='1'
                        if week==' Четная':
                            subject.weeks='2'
                    else:
                        subject.weeks='12'
                    similar=Subject.objects.filter(title=subject.title,owner=user)
                    if len(similar)>0:
                        subject.color=similar[0].color
                        subject.image=similar[0].image
                    else:
                        subject.color = random.choice(colors)
                        #subject.image = f'/static/images/icons/{random.choice(Image.objects.all()).path}'
                    subject.save()
                    days=Day.objects.filter(owner=user).order_by('date')
                    if settings.exams_date:
                        exams_start = settings.exams_date
                    else:
                        exams_start = settings.end_date
                    for day in days:
                        if day.date <= exams_start:
                            day_week = day.week % settings.repeating_weeks
                            if day_week == 0:
                                day_week = settings.repeating_weeks
                            day_week = str(day_week)
                            if day.weekday == subject.weekday and day_week in subject.weeks:
                                lesson = Lesson()
                                lesson = create_lessons(subject, lesson)
                                lesson.select_subject = subject
                                lesson.title = subject.title
                                lesson.time = subject.time
                                lesson.start_time = subject.start_time
                                lesson.end_time = subject.end_time
                                lesson.date = day.date
                                lesson.type = subject.type
                                lesson.owner = user
                                lesson.save()

def get_today(user):
    try:
        today = Day.objects.get(date=datetime.today(), owner=user)
    except:
        start_point = Day.objects.filter(weekday=datetime.today().weekday()).order_by('date')[0].date
        count_week = 1 + (datetime.now().timestamp() - int(
            datetime.combine(start_point, datetime.now().time()).timestamp())) / seconds_in_week
        today = Day.objects.create(date=datetime.today(), owner=user, weekday=datetime.today().weekday(),
                                   week=count_week)
    return today
def get_day(user,date):
    try:
        day = Day.objects.get(date=date, owner=user)
    except:
        start_point = Day.objects.filter(weekday=date.weekday()).order_by('date')[0].date
        now=datetime.combine(date, datetime.now().time())
        count_week = 1 + (now.timestamp() - int(
            datetime.combine(start_point, datetime.now().time()).timestamp())) / seconds_in_week
        day = Day.objects.create(date=date, owner=user, weekday=date.weekday(),
                                   week=count_week)
    return day
def get_tomorrow(user):
    try:
        tomorrow = Day.objects.get(date=datetime.today() + timedelta(days=1), owner=user)
    except:
        tomorrow=None
        #start_point = Day.objects.filter(weekday=datetime.today().weekday()).order_by('date')[0].date
        #count_week = 1 + (datetime.now().timestamp() - int(datetime.combine(start_point, datetime.now().time()).timestamp())+seconds_in_day) / seconds_in_week
        #tomorrow = Day.objects.create(date=datetime.today() + timedelta(days=1), owner=user, week=count_week, weekday=datetime.today().weekday())
    return tomorrow

def start(request):
    with open('MSP/universities.json', 'r', encoding='utf-8') as js:
        universities = json.load(js)
    nsu=False
    nsu_import=False
    step = "dates"
    if request.user.is_authenticated:
        user = request.user
    settings = get_object_or_404(Settings, owner=user)
    settings_form = SettingsForm(instance=settings)
    semester_form = SemesterForm(instance=settings)
    schedule = Time.objects.filter(owner=user)
    schedule_forms = []
    for time in schedule:
        schedule_forms.append(TimeForm(request.POST, instance=time))
    palette = dict(zip(colors, sub_colors))
    if request.method == "POST":
        if "save_color" in request.POST:
            step = 'appearance'
            settings.theme = request.POST["color"]
            settings.sub_color = palette[settings.theme]
            settings.save()
            return redirect('subjects')
        if "save_dates" in request.POST:
            step = 'university'
            f = 0
            semester_form = SemesterForm(request.POST, instance=settings)
            if semester_form.has_changed():
                semester = semester_form.save(commit=False)
                semester.save()
                settings.start_date = semester.start_date
                settings.end_date = semester.end_date
                settings.save()
                Day.objects.filter(owner=user).delete()
                start_date = int(datetime.combine(settings.start_date, datetime.now().time()).timestamp())
                end_date = int(datetime.combine(settings.end_date, datetime.now().time()).timestamp())
                d = start_date
                week = 1
                while d <= end_date:
                    day = Day()
                    day.date = datetime.fromtimestamp(d).date()
                    day.weekday = datetime.fromtimestamp(d).weekday()
                    day.week = week
                    day.owner = user
                    day.save()
                    if day.weekday == 6:
                        week += 1
                    d += 86400
            try:
                settings.exams_date = request.POST['exams_date']
                settings.save()
            except:
                pass
            for i in range(8):
                try:
                    holiday_start = request.POST[f'holiday_start{i}']
                    holiday_end = request.POST[f'holiday_end{i}']
                    holiday = Holiday(start_date=holiday_start, end_date=holiday_end, owner=user)
                    holiday.save()
                    settings.holidays.add(holiday)
                    settings.save()
                except:
                    pass

        elif "save_auto" in request.POST:
            step = "schedule"
            settings_form = SettingsForm(request.POST, instance=settings)
            if settings_form.is_valid():
                settings = settings_form.save(commit=False)
                settings.save()
                schedule.delete()
                create_times(settings,user)
                for time in schedule:
                    time_form = TimeForm(request.POST, instance=time)
                    if time_form.is_valid():
                        time_form = time_form.save(commit=False)
                        time_form.save()
        elif "save_manual" in request.POST:
            step = "schedule"
            for time in schedule:
                time_form = TimeForm(request.POST, instance=time)
                if time_form.is_valid():
                    time = time_form.save(commit=False)
                    time.start_time = request.POST["start_time" + str(time.number)]
                    time.end_time = request.POST["end_time" + str(time.number)]
                    time.owner = user
                    time.save()
        elif "save_university" in request.POST:
            settings.university=request.POST["select_university"]
            if request.POST["other"]=="True":
                settings.university = request.POST["other_university"]
            settings.save()
            if settings.university=='НГУ':
                step="import"
            else:
                step="schedule"
        elif "import_timetable" in request.POST:
            group = request.POST['group']
            load_subjects_html(group, user, settings)
            step = "appearance"
            nsu_import=True
        elif "move_to_last" in request.POST:
            step="appearance"

    else:
        start_date = Day.objects.get(date=settings.start_date,owner=user)
        end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request,'MSP/start.html',{'semester_form':semester_form,'step':step,'schedule':schedule,'schedule_forms':schedule_forms,'settings':settings,'settings_form':settings_form,'nsu':nsu,'colors':colors,'nsu_import':nsu_import,'universities':universities,'compliment_colors':palette})

def dashboard(request):
    if request.user.is_authenticated:
        user = request.user
        settings=Settings.objects.get(owner=user)
        today=get_today(user)
        if 'timetable' in settings.homepage:
            return redirect(settings.homepage, pk=today.pk)
        else:
            return redirect(settings.homepage)
    else:
        return redirect('login')

def info(request, pk):
    if request.user.is_authenticated:
        user = request.user
    lesson = get_object_or_404(Lesson, pk=pk)
    hometasks = Hometask.objects.filter(lesson=lesson)
    exams = Exam.objects.filter(lesson=lesson)
    time_now = datetime.now().time()
    today=get_today(user)
    if request.method == "GET":
        for task in hometasks:
            if ('done_' + str(task.pk)) in request.GET:
                done = request.GET['done_' + str(task.pk)]
                task.done = done == 'True'
                task.save()
    return render(request, 'MSP/info.html',
                  {'lesson': lesson, 'hometasks': hometasks, 'exams': exams, 'time_now': time_now, 'today': today})


def notes_lesson(request, pk):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    lesson = get_object_or_404(Lesson, pk=pk)
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.save(update_fields=['notes'])
            return redirect('notes_lesson', pk=pk)
    else:
        form = LessonForm(instance=lesson)
    return render(request, 'MSP/notes.html', {'form': form, 'pk': pk, 'settings': settings})


def notes_task(request, pk):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    task = get_object_or_404(Hometask, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.save(update_fields=['notes'])
            task = get_object_or_404(Hometask, pk=pk)
            return redirect('info', pk=task.lesson.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'MSP/notes.html', {'form': form, 'pk': pk, 'settings': settings})


def notes_exam(request, pk):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=exam)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.save(update_fields=['notes'])
            exam = get_object_or_404(Exam, pk=pk)
            return redirect('notes_exam', pk=pk)
    else:
        form = TaskForm(instance=exam)
    return render(request, 'MSP/notes.html', {'form': form, 'pk': pk, 'settings': settings, 'exam': exam})


def notes_plan(request, pk):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.save(update_fields=['notes'])
            plan = get_object_or_404(Plan, pk=pk)
            return redirect('notes_plan', pk=pk)
    else:
        form = TaskForm(instance=plan)
    return render(request, 'MSP/notes.html', {'form': form, 'pk': pk, 'settings': settings, 'plan': 'plan'})

def import_timetable(request):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    today = Day.objects.get(date=datetime.today(), owner=user)
    if request.method == "POST":
        group=request.POST['group']
        load_subjects_html(group,user,settings)
        return redirect('subjects')
    else:
        return render(request,'MSP/import.html',{'settings':settings,'today':today})


def timetable(request, pk):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    times = Time.objects.filter(owner=user)
    days = Day.objects.filter(owner=user).order_by('date')
    day = get_object_or_404(Day, pk=pk)
    if request.method=='POST':
        go_to_date = request.POST['go_to_date_real']
        go_to_date=datetime.strptime(go_to_date,'%Y-%m-%d').date()
        go = get_day(user, go_to_date)
        return redirect('timetable', pk=go.pk)
        try:
            go_to_date = request.POST['go_to_date_real']
            go = get_day(user,go_to_date)
            return redirect('timetable', pk=go.pk)
        except:
            pass

    lessons = Lesson.objects.filter(owner=user, date=day.date).order_by('start_time')
    show_windows = dict(zip([time.number for time in times], [[] for i in range(settings.max_lessons)]))
    for time in times:
        for lesson in lessons:
            if lesson.time == time.number:
                show_windows[time.number].append(lesson)
    i = -1
    while -i < len(show_windows):
        key = list(show_windows.keys())[i]
        if show_windows[key] == []:
            show_windows[key] = 'delete'
        else:
            break
        i -= 1
    for key in tuple(show_windows.keys()):
        if show_windows[key] == 'delete':
            del show_windows[key]
    first_lesson_today = 1
    key = 1
    while (key <= len(show_windows.keys())):
        if show_windows[key] != []:
            break
        key += 1
    if len(lessons) == 0:
        weekend = True
    else:
        weekend = False
    if list(show_windows.values()) == []:
        toggle = 0
    else:
        toggle = 1
    today = get_today(user)
    time_now = datetime.now().time()
    date = day.date
    weeknum = day.weekday
    weekday = weekdays[weeknum]
    hometasks = Hometask.objects.filter(lesson__in=lessons)
    dict_lessons = {lesson.pk: 0 for lesson in lessons}
    for hometask in hometasks:
        dict_lessons.update({hometask.lesson.pk: hometask.pk})
    hometasks = hometasks.filter(pk__in=dict_lessons.values())
    exams = Exam.objects.filter(owner=user)
    if request.method == "GET":
        for task in hometasks:
            if ('done_' + str(task.pk) + '_0') in request.GET:
                done = request.GET['done_' + str(task.pk) + '_0']
                task.done = done == 'True'
                task.save()
            if ('done_' + str(task.pk) + '_1') in request.GET:
                done = request.GET['done_' + str(task.pk) + '_1']
                task.done = done == 'True'
                task.save()
    yesterday=Day.objects.filter(pk__lt=day.pk, owner=user)
    tomorrow=Day.objects.filter(pk__gt=day.pk, owner=user)
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    holiday=False
    for h in settings.holidays.all():
        if h.start_date <= day.date <= h.end_date:
            holiday=True
    return render(request, 'MSP/timetable.html',
                  {'lessons': lessons, 'hometasks': hometasks, 'exams': exams, 'date': date, 'weekday': weekday,
                   'weeknum': weeknum, 'settings': settings, 'day': day, 'pk': day.pk, 'today': today,
                   'show_windows': show_windows, 'times': times, 'first_lesson_today': key, 'time_now': time_now,
                   'weekend': weekend, 'toggle': toggle, 'days': days,'yesterday':yesterday,'tomorrow':tomorrow,'start_date':start_date,'end_date':end_date,'holiday':holiday})


def lesson_new(request):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    today = Day.objects.get(date=datetime.today(), owner=user)
    images = Image.objects.all()
    settings = Settings.objects.get(owner=user)
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            try:
                lesson.date = request.POST["date"]
            except:
                pass
            color = request.POST["color"]
            lesson.color = color
            try:
                lesson_time = Time.objects.get(number=lesson.time, owner=user)
                if not lesson.start_time and lesson_time:
                    lesson.start_time = lesson_time.start_time
                    lesson.end_time = lesson_time.end_time
            except:
                pass
            try:
                if not lesson.end_time and lesson_time:
                    lesson_delta = timedelta(minutes=settings.lesson_length)
                    lesson.end_time = (datetime.combine(date.today(), lesson.start_time) + lesson_delta).time()
            except:
                pass
            select_image = request.POST["select-image"]
            lesson.image = select_image
            select_image_link = request.POST["select-image-link"]
            if select_image_link:
                lesson.image = select_image_link
            subject = lesson.select_subject
            if subject:
                lesson.title = lesson.select_subject.title
                lesson.time = subject.time
                lesson.type=subject.type
                if not lesson.start_time:
                    lesson.start_time = subject.start_time
                if not lesson.end_time:
                    lesson.end_time = subject.end_time
                lesson = create_lessons(subject, lesson)
            if lesson.teacher:
                teacher = lesson.teacher.split(' ')
                try:
                    lesson.teachershort = ''.join([teacher[0], ' ', teacher[1][0], '.', teacher[2][0], '.'])
                except:
                    lesson.teachershort=lesson.teacher
            else:
                lesson.teachershort = ''
            if lesson.title:
                lesson.title_short = shorten_title(lesson.title)
            lesson.date = datetime.strptime(lesson.date, '%Y-%m-%d')
            lesson.weekday = lesson.date.weekday()
            lesson.owner = user
            lesson.save()
            return redirect('timetable', pk=today.pk)
    else:
        form = LessonForm({"user": user})
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/lesson_edit.html',
                  {'form': form, 'colors': colors, 'settings': settings, 'images': images, 'today': today,
                   'subjects': subjects,'start_date':start_date,'end_date':end_date})


def lesson_edit(request, pk,page,fix_day):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    today = Day.objects.get(date=datetime.today(), owner=user)
    images = Image.objects.all()
    settings = Settings.objects.get(owner=user)
    lesson = get_object_or_404(Lesson, pk=pk)
    title_initial=lesson.title
    subject_initial=lesson.select_subject
    title_initial=lesson.title
    type_initial=lesson.type
    color_initial=lesson.color
    teacher_initial= lesson.teacher
    classroom_initial= lesson.classroom
    image_initial=lesson.image
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)
            try:
                lesson.date = request.POST["date"]
            except:
                pass
            if lesson.teacher:
                teacher = lesson.teacher.split(' ')
                try:
                    lesson.teachershort = ''.join([teacher[0], ' ', teacher[1][0], '.', teacher[2][0], '.'])
                except:
                    pass
            else:
                lesson.teachershort = ''
            color = request.POST["color"]
            lesson.color = color
            lesson.date = datetime.strptime(lesson.date, '%Y-%m-%d')
            lesson.weekday = lesson.date.weekday()
            if form['select_subject']!=subject_initial:
                subject=lesson.select_subject
                lesson.select_subject = subject
                if lesson.title == title_initial:
                    lesson.title = subject.title
                    lesson.title_short = subject.title_short
                if lesson.type == type_initial:
                    lesson.type = subject.type
                if lesson.color == color_initial:
                    lesson.color=subject.color
                if lesson.teacher == teacher_initial:
                    lesson.teacher = subject.teacher
                    lesson.teachershort = subject.teachershort
                if lesson.classroom == classroom_initial:
                    lesson.classroom = subject.classroom
                if lesson.image == image_initial:
                    lesson.image = subject.image

            try:
                lesson_time = Time.objects.get(number=lesson.time, owner=user)
                if lesson_time:
                    lesson.start_time = lesson_time.start_time
                    lesson.end_time = lesson_time.end_time
            except:
                pass
            try:
                if not lesson.end_time and lesson_time:
                    lesson_delta = timedelta(minutes=settings.lesson_length)
                    lesson.end_time = (datetime.combine(date.today(), lesson.start_time) + lesson_delta).time()
            except:
                pass
            select_image = request.POST["select-image"]
            lesson.image = select_image
            select_image_link = request.POST["select-image-link"]
            if select_image_link:
                lesson.image = select_image_link
            lesson.save()
            if not lesson.title or lesson.title!=title_initial:
                lesson.title_short = shorten_title(lesson.title)
                lesson.save()
            return redirect(page, pk=fix_day)
    else:
        form = LessonForm(instance=lesson, initial={"user": user})
        start_date = Day.objects.get(date=settings.start_date,owner=user)
        end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/lesson_edit.html',
                  {'pk': lesson.pk, 'form': form, 'colors': colors, 'lesson': lesson, 'settings': settings,
                   'images': images, 'today': today, 'subjects': subjects,'page':page,'fix_day':fix_day,'start_date':start_date,'end_date':end_date})


def lesson_delete(request, pk, page,fix_day):
    if request.user.is_authenticated:
        user = request.user
    today = Day.objects.get(date=datetime.today(), owner=user)
    lesson = get_object_or_404(Lesson, pk=pk)
    lesson.delete()
    return redirect(page, pk=fix_day)

def settings(request,unit='dates'):
    with open('MSP/universities.json', 'r', encoding='utf-8') as js:
        universities = json.load(js)
    if request.user.is_authenticated:
        user = request.user
    schedule = Time.objects.filter(owner=user)
    settings = get_object_or_404(Settings, owner=user)
    if request.method == "POST":
        if "save_misc" in request.POST:
            settings.theme = request.POST["color"]
            settings.sub_color = palette[settings.theme]
            settings.homepage = request.POST['homepage']
            settings.save()
            return redirect('settings', unit='misc')
        if "save_dates" in request.POST:
            f = 0
            semester_form = SemesterForm(request.POST, instance=settings)
            if semester_form.is_valid():
                semester = semester_form.save(commit=False)
                semester.save()
                settings.start_date = semester.start_date
                settings.end_date = semester.end_date
                settings.save()
                Day.objects.filter(owner=user).delete()
                start_date = int(datetime.combine(settings.start_date, datetime.now().time()).timestamp())
                end_date = int(datetime.combine(settings.end_date, datetime.now().time()).timestamp())
                d = start_date
                week = 1
                while d <= end_date:
                    day = Day()
                    day.date = datetime.fromtimestamp(d).date()
                    day.weekday = datetime.fromtimestamp(d).weekday()
                    day.week = week
                    day.owner = user
                    day.save()
                    if day.weekday == 6:
                        week += 1
                    d += 86400
            try:
                settings.exams_date = request.POST['exams_date']
                settings.save()
            except:
                settings.exams_date=None
                settings.save()
            try:
                to_del = request.POST['holidays_to_delete'].split('_')
                for h in to_del:
                    Holiday.objects.get(pk=h).delete()
            except:
                pass
            for i in range(8):
                try:
                    holiday_start = request.POST[f'holiday_start{i}']
                    holiday_end = request.POST[f'holiday_end{i}']
                    holiday = Holiday(start_date=holiday_start, end_date=holiday_end, owner=user)
                    holiday.save()
                    settings.holidays.add(holiday)
                    settings.save()
                except:
                    pass
            return redirect('settings', unit='dates')
        elif "save_auto" in request.POST:
            settings_form = SettingsForm(request.POST, instance=settings)
            if settings_form.is_valid():
                settings = settings_form.save(commit=False)
                settings.save()
                schedule.delete()
                create_times(settings,user)
                for time in schedule:
                    time_form = TimeForm(request.POST, instance=time)
                    if time_form.is_valid():
                        time_form = time_form.save(commit=False)
                        time_form.save()
            return redirect('settings', unit='schedule')
        elif "save_manual" in request.POST:
            for time in schedule:
                time_form = TimeForm(request.POST, instance=time)
                if time_form.is_valid():
                    time = time_form.save(commit=False)
                    time.start_time = request.POST["start_time" + str(time.number)]
                    time.end_time = request.POST["end_time" + str(time.number)]
                    time.owner = user
                    time.save()
            return redirect('settings', unit='schedule')
        elif "save_university" in request.POST:
            try:
                settings.university=request.POST["select_university"]
            except:
                pass
            if request.POST["other"]=="True":
                settings.university = request.POST["other_university"]
            settings.save()
            return redirect('settings', unit='misc')
        elif "import_timetable" in request.POST:
            group = request.POST['group']
            load_subjects_html(group, user, settings)
            return redirect('settings', unit='misc')
    else:
        settings = get_object_or_404(Settings, owner=user)
        today = get_today(user)
        settings_form = SettingsForm(instance=settings)
        semester_form = SemesterForm(instance=settings)
        schedule_forms = []
        for time in schedule:
            schedule_forms.append(TimeForm(request.POST, instance=time))
        start_date = Day.objects.get(date=settings.start_date,owner=user)
        end_date = Day.objects.get(date=settings.end_date,owner=user)
        return render(request, 'MSP/settings.html',
                      {'settings_form': settings_form, 'colors': colors, 'settings': settings, 'schedule': schedule,
                       'schedule_forms': schedule_forms, 'semester_form': semester_form, 'today': today, 'user': user,'start_date':start_date,'end_date':end_date,'unit':unit,'universities':universities})


def tasks(request):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    today = get_today(user)
    tomorrow=get_tomorrow(user)
    tasks = Hometask.objects.filter(owner=user).order_by('date')
    if len(tasks) == 0:
        empty = True
    else:
        empty = False
    for task in tuple(tasks):
        if task.done == True and task.date + timedelta(days=7) < today.date:
            task.delete()
    if request.method == "GET":
        if 'delete_done' in request.GET:
            for task in tuple(tasks):
                if task.done:
                    task.delete()
                    return redirect('tasks')
        else:
            for task in tasks:
                if ('done_' + str(task.pk)) in request.GET:
                    done = request.GET['done_' + str(task.pk)]
                    task.done = done == 'True'
                    task.save()
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/tasks.html',
                  {'today': today, 'tomorrow': tomorrow, 'settings': settings, 'tasks': tasks,
                   'weekdays': weekdays_short, 'empty': empty,'start_date':start_date,'end_date':end_date})


def task_new(request):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    lessons = Lesson.objects.filter(owner=user)
    today=get_today(user)
    settings = Settings.objects.get(owner=user)
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)

            try:
                deadline_date = request.POST["deadline_date"]
                task.date = datetime.strptime(deadline_date, '%Y-%m-%d')
                task.weekday = task.date.weekday()
            except:
                pass
            try:
                deadline_subject = request.POST["deadline_subject"]
            except:
                pass
            try:
                subject = subjects.get(pk=deadline_subject)
                task.select_subject = subject
                task.lesson = lessons.get(date=deadline_date, select_subject=subject, start_time=subject.start_time,
                                          owner=user)
                task.date = task.lesson.date
                task.weekday = task.date.weekday()
            except:
                pass

            try:
                task.select_subject = task.lesson.select_subject
                task.date = task.lesson.date
                task.weekday = task.date.weekday()
            except:
                pass
            task.owner = user
            task.save()
            return redirect('tasks')
    else:
        try:
            time_now = datetime.now()
            now_lesson = Lesson.objects.get(date=time_now.date(), start_time__lte=time_now.time(),
                                            end_time__gte=time_now.time())
            now_subject = list(
                Lesson.objects.filter(select_subject__title=now_lesson.title,select_subject__type=now_lesson.type))
            now_index = now_subject.index(now_lesson)
            next = now_subject[now_index + 1]
            next_subject=next.select_subject
            next=next.pk
        except:
            next=None
            next_subject = None
        form = TaskForm(initial={'lesson':next})
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/task_edit.html',
                  {'subjects': subjects, 'form': form, 'settings': settings, 'today': today,'start_date':start_date,'end_date':end_date,'next':next_subject})


def task_edit(request, pk):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    today = get_today(user)
    settings = Settings.objects.get(owner=user)
    task = get_object_or_404(Hometask, pk=pk)
    lessons = Lesson.objects.filter(owner=user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            try:
                deadline_date = request.POST["deadline_date"]
                task.date = datetime.strptime(deadline_date, '%Y-%m-%d')
                task.weekday = task.date.weekday()
            except:
                pass
            try:
                deadline_subject = request.POST["deadline_subject"]
            except:
                pass
            try:
                subject = subjects.get(pk=deadline_subject)
                task.select_subject = subject
                task.lesson = lessons.get(date=deadline_date, select_subject=subject, owner=user)
                task.date = task.lesson.date
                task.weekday = task.date.weekday()
            except:
                pass
            try:
                task.select_subject = task.lesson.select_subject
                task.date = task.lesson.date
                task.weekday = task.date.weekday()
            except:
                pass
            task.save()
            return redirect('tasks')
    else:
        form = TaskForm(instance=task)
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/task_edit.html',
                  {'subjects': subjects, 'pk': task.pk, 'form': form, 'task': task, 'settings': settings,
                   'today': today,'start_date':start_date,'end_date':end_date})


def task_delete(request, pk):
    if request.user.is_authenticated:
        user = request.user
    today = get_today(user)
    task = get_object_or_404(Hometask, pk=pk)
    task.delete()
    return redirect('tasks')

def subject_double(request,pk):
    subject=Subject.objects.get(pk=pk)
    clone=subject.clone()
    settings=Settings.objects.get(owner=subject.owner)
    if settings.exams_date:
        exams_start = settings.exams_date
    else:
        exams_start = settings.end_date
    days = Day.objects.filter(owner=subject.owner, date__lte=exams_start)
    for day in days:
        day_week = day.week % settings.repeating_weeks
        if day_week == 0:
            day_week = settings.repeating_weeks
        day_week = str(day_week)
        if day.weekday == subject.weekday and day_week in subject.weeks:
            lesson = Lesson()
            lesson = create_lessons(subject, lesson)
            lesson.select_subject = subject
            lesson.title = subject.title
            lesson.time = subject.time
            lesson.start_time = subject.start_time
            lesson.end_time = subject.end_time
            lesson.date = day.date
            lesson.type = subject.type
            lesson.owner = subject.owner
            lesson.save()
    return redirect('subjects')

def subject_new(request):
    if request.user.is_authenticated:
        user = request.user
    days = Day.objects.filter(owner=user)
    today=get_today(user)
    images = Image.objects.all()
    settings = Settings.objects.get(owner=user)
    schedule = Time.objects.filter(owner=user)
    weekrange = range(1, settings.repeating_weeks + 1)
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            if subject.teacher:
                teacher = subject.teacher.split(' ')
                subject.teachershort = ''.join([teacher[0], ' ', teacher[1][0], '.', teacher[2][0], '.'])
            else:
                subject.teachershort = ''
            if subject.title:
                subject.title_short = shorten_title(subject.title)
            if settings.repeating_weeks > 1:
                weeks_str = ''
                for i in weekrange:
                    if request.POST[str(i)]:
                        weeks_str += str(i)
                subject.weeks = weeks_str
            color = request.POST["color"]
            subject.color = color
            try:
                subject_time = schedule.get(number=subject.time, owner=user)
                if not subject.start_time:
                    subject.start_time = subject_time.start_time
                    subject.end_time = subject_time.end_time
            except:
                pass
            if not subject.end_time:
                subject_delta = timedelta(minutes=settings.lesson_length)
                subject.end_time = (datetime.combine(date.today(), subject.start_time) + subject_delta).time()
            select_image = request.POST["select-image"]
            subject.image = select_image
            select_image_link = request.POST["select-image-link"]
            if select_image_link:
                subject.image = select_image_link
            subject.owner = user
            subject.save()
            if settings.exams_date:
                exams_start=settings.exams_date
            else:
                exams_start=settings.end_date
            for day in days:
                if day.date<=exams_start:
                    day_week = day.week % settings.repeating_weeks
                    if day_week == 0:
                        day_week = settings.repeating_weeks
                    day_week = str(day_week)
                    if day.weekday == subject.weekday and day_week in subject.weeks:
                        lesson = Lesson()
                        lesson = create_lessons(subject, lesson)
                        lesson.select_subject = subject
                        lesson.title = subject.title
                        lesson.time = subject.time
                        lesson.start_time = subject.start_time
                        lesson.end_time = subject.end_time
                        lesson.date = day.date
                        lesson.type = subject.type
                        lesson.owner = user
                        lesson.save()
            return redirect('subjects')
    else:
        form = SubjectForm()
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/subject_edit.html',
                  {'form': form, 'colors': colors, 'settings': settings, 'images': images, 'today': today,
                   'range': weekrange,'start_date':start_date,'end_date':end_date})


def task_new_lesson(request, lesson, date, time, menu, info):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    lessons = Lesson.objects.filter(owner=user)
    today=get_today(user)
    settings = Settings.objects.get(owner=user)
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            this_lesson = lessons.get(title=lesson, date=date, start_time=time, owner=user)
            deadline_subject = this_lesson.select_subject
            this_or_next = request.POST["this_or_next"]
            deadline_date = request.POST["deadline_date"]
            if this_or_next == 'this':
                task.lesson = this_lesson
            elif this_or_next == 'next':
                lessons = list(lessons)
                n = lessons.index(this_lesson)
                next_lesson = lessons[n + 1]
                task.lesson = next_lesson
            if task.lesson:
                task.select_subject = task.lesson.select_subject
                task.date = task.lesson.date
            else:
                task.select_subject = deadline_subject
                if deadline_date != '':
                    task.date = datetime.strptime(deadline_date, '%Y-%m-%d')
            if task.date:
                task.weekday = task.date.weekday()
            task.owner = user
            task.save()
            if menu == '1':
                return redirect('tasks')
            else:
                return redirect('info', pk=info)
    else:
        form = TaskForm()
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/task_edit_lesson.html',
                  {'subjects': subjects, 'form': form, 'settings': settings, 'today': today, 'menu': menu,'start_date':start_date,'end_date':end_date})


def subjects(request):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user).order_by('weekday', 'start_time','end_time','title',)
    today=get_today(user)
    settings = Settings.objects.get(owner=user)
    start_date=Day.objects.get(date=settings.start_date)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/subjects.html',
                  {'subjects': subjects, 'settings': settings, 'today': today, 'weekdays': weekdays,'start_date':start_date,'end_date':end_date,'start_date':start_date,'end_date':end_date})


def subject_edit(request, pk):
    if request.user.is_authenticated:
        user = request.user
    days = Day.objects.filter(owner=user)
    settings = Settings.objects.get(owner=user)
    today=get_today(user)
    images = Image.objects.all()
    schedule = Time.objects.filter(owner=user)
    lessons = Lesson.objects.filter(owner=user)
    weekrange = range(1, settings.repeating_weeks + 1)
    subject = get_object_or_404(Subject, pk=pk)
    weekday_initial = subject.weekday
    weeks_initial = subject.weeks
    title_initial=subject.title
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save(commit=False)
            if subject.teacher:
                teacher = subject.teacher.split(' ')
                try:
                    subject.teachershort = ''.join([teacher[0], ' ', teacher[1][0], '.', teacher[2][0], '.'])
                except:
                    pass
            else:
                subject.teachershort = ''
            if settings.repeating_weeks > 1:
                weeks_str = ''
                for i in weekrange:
                    if request.POST[str(i)] != 'False':
                        weeks_str += str(i)
                subject.weeks = weeks_str
            color = request.POST["color"]
            subject.color = color
            try:
                subject_time = schedule.get(number=subject.time, owner=user)
                if not subject.start_time:
                    subject.start_time = subject_time.start_time
                    subject.end_time = subject_time.end_time
            except:
                pass
            if not subject.end_time:
                subject_delta = timedelta(minutes=settings.lesson_length)
                subject.end_time = (datetime.combine(date.today(), subject.start_time) + subject_delta).time()
            select_image = request.POST["select-image"]
            subject.image = select_image
            select_image_link = request.POST["select-image-link"]
            if select_image_link:
                subject.image = select_image_link
            subject.save()
            if not subject.title or subject.title!=title_initial:
                subject.title_short = shorten_title(subject.title)
                subject.save()
            if subject.weekday != weekday_initial or subject.weeks != weeks_initial:
                lessons.filter(select_subject=subject).delete()
                if settings.exams_date:
                    exams_start = settings.exams_date
                else:
                    exams_start = settings.end_date
                for day in days:
                    if day.date <= exams_start:
                        day_week = day.week % settings.repeating_weeks
                        if day_week == 0:
                            day_week = settings.repeating_weeks
                        day_week = str(day_week)
                        if day.weekday == subject.weekday and day_week in subject.weeks:
                            lesson = Lesson()
                            lesson = create_lessons(subject, lesson)
                            lesson.select_subject = subject
                            lesson.title = subject.title
                            lesson.time = subject.time
                            lesson.start_time = subject.start_time
                            lesson.end_time = subject.end_time
                            lesson.date = day.date
                            lesson.type = subject.type
                            lesson.owner = user
                            lesson.save()
            else:
                for lesson in lessons:
                    if lesson.select_subject == subject:
                        lesson = create_lessons(subject, lesson)
                        lesson.title = subject.title
                        lesson.time = subject.time
                        lesson.start_time = subject.start_time
                        lesson.end_time = subject.end_time
                        lesson.save()
            return redirect('subjects')
    else:
        form = SubjectForm(instance=subject)
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/subject_edit.html',
                  {'subject': subject, 'form': form, 'colors': colors, 'settings': settings, 'images': images,
                   'today': today, 'pk': pk, 'range': weekrange,'start_date':start_date,'end_date':end_date})


def subject_delete(request, pk):
    if request.user.is_authenticated:
        user = request.user
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    return redirect('subjects')


def exams(request):
    if request.user.is_authenticated:
        user = request.user
    settings=Settings.objects.get(owner=user)
    today = get_today(user)
    tomorrow=get_tomorrow(user)
    examinations = []
    other = []
    exams = Exam.objects.filter(owner=user).order_by('date')
    for exam in exams:
        if exam.examination:
            examinations.append(exam)
        else:
            other.append(exam)
    now = datetime.now().timestamp()
    meta = None
    days_left = None
    semester = None
    passed = None
    empty = False
    if len(exams) == 0:
        empty = True
    elif len(examinations) > 0:
        first_exam = datetime.combine(examinations[0].date, datetime.now().time()).timestamp()
        days_left = int((first_exam - now) // (60 * 60 * 24))
        if days_left % 10 == 1 and days_left % 100 != 11:
            meta = 1
        elif days_left % 10 in [2, 3, 4] and days_left % 100 in [12, 13, 14]:
            meta = 2
        else:
            meta = 0
        start_date = datetime.combine(settings.start_date, datetime.now().time()).timestamp()
        end_date = datetime.combine(settings.end_date, datetime.now().time()).timestamp()
        semester = int((end_date - start_date) // (60 * 60 * 24))
        passed = int((now - start_date) // (60 * 60 * 24))
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    treshold=datetime.today().date()-timedelta(days=7)
    delete_exams=Exam.objects.filter(date__lt=treshold)
    for ex in delete_exams:
        ex.delete()
    return render(request, 'MSP/exams.html',
                  {'today': today, 'tomorrow': tomorrow, 'settings': settings, 'exams': exams,
                   'weekdays': weekdays_short, 'examinations': examinations, 'other': other, 'days_left': days_left,
                   'meta': meta, 'semester': semester, 'passed': passed, 'empty': empty,'start_date':start_date,'end_date':end_date})


def exam_edit(request, pk):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    today=get_today(user)
    settings = Settings.objects.get(owner=user)
    exam = get_object_or_404(Exam, pk=pk)
    lessons = Lesson.objects.filter(owner=user)
    if request.method == "POST":
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            exam = form.save(commit=False)
            try:
                deadline_date = request.POST["deadline_date"]
                deadline_subject = request.POST["deadline_subject"]
                exam.date = datetime.strptime(deadline_date, '%Y-%m-%d')
                exam.weekday = exam.date.weekday()
            except:
                pass
            try:
                subject = subjects.get(pk=deadline_subject)
                exam.select_subject = subject
                exam.lesson = lessons.get(date=deadline_date, select_subject=subject, owner=user)
                exam.date = exam.lesson.date
                exam.weekday = exam.date.weekday()
            except:
                pass
            try:
                exam.select_subject = exam.lesson.select_subject
                exam.date = exam.lesson.date
                exam.weekday = exam.date.weekday()
            except:
                pass
            if exam.lesson:
                exam.start_time = exam.lesson.start_time
            try:
                exam_time = Time.objects.get(number=exam.time, owner=user)
                if not exam.start_time:
                    exam.start_time = exam_time.start_time
            except:
                pass
            exam.save()
            if not exam.type:
                if exam.examination:
                    exam.type = 'экзамен'
                else:
                    exam.type = 'контрольная'
            exam.save()
            return redirect('exams')
    else:
        form = ExamForm(instance=exam)
        examination = exam.examination == 'examination'
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/exam_edit.html',
                  {'subjects': subjects, 'pk': exam.pk, 'form': form, 'exam': exam, 'settings': settings,
                   'today': today, 'examination': examination,'start_date':start_date,'end_date':end_date})


def exam_new(request, exam, lessons, subjects,examination):
    if request.user.is_authenticated:
        user = request.user
    try:
        exam.examination = request.POST['examination']
    except:
        exam.examination=examination

    try:
        deadline_date = request.POST["deadline_date"]
        deadline_subject = request.POST["deadline_subject"]
        exam.date = datetime.strptime(deadline_date, '%Y-%m-%d')
        exam.weekday = exam.date.weekday()
    except:
        pass
    try:
        subject = subjects.get(pk=deadline_subject)
        exam.select_subject = subject
        exam.lesson = lessons.get(date=deadline_date, select_subject=subject, owner=user)
        exam.date = exam.lesson.date
        exam.weekday = exam.date.weekday()
    except:
        pass

    try:
        exam.select_subject = exam.lesson.select_subject
        exam.date = exam.lesson.date
        exam.weekday = exam.date.weekday()
    except:
        pass
    if exam.lesson:
        exam.start_time = exam.lesson.start_time
    try:
        exam_time = Time.objects.get(number=exam.time, owner=user)
        if not exam.start_time:
            exam.start_time = exam_time.start_time
    except:
        pass
    exam.owner = user
    exam.save()
    if not exam.type:
        if exam.examination:
            exam.type = 'экзамен'
        else:
            exam.type = 'контрольная'
    exam.save()
    return exam


def exam_new_1(request):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    today=get_today(user)
    settings = Settings.objects.get(owner=user)
    lessons = Lesson.objects.filter(owner=user)
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam = exam_new(request, exam, lessons, subjects,False)
            exam.save()
            return redirect('exams')
    else:
        form = ExamForm()
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/exam_edit.html',
                  {'subjects': subjects, 'form': form, 'settings': settings, 'today': today,'start_date':start_date,'end_date':end_date})


def exam_new_2(request, examination):
    if request.user.is_authenticated:
        user = request.user
    subjects = Subject.objects.filter(owner=user)
    today=get_today(user)
    settings = Settings.objects.get(owner=user)
    lessons = Lesson.objects.filter(owner=user)
    if request.method == "POST":
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam = exam_new(request, exam, lessons, subjects,examination=='examination')
            exam.examination=examination=='examination'
            exam.owner = user
            exam.save()
            return redirect('exams')
    else:
        examination = examination == 'examination'
        if examination:
            form = ExamForm({'type': 'экзамен'})
        else:
            form = ExamForm({'type': 'контрольная'})
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/exam_edit.html',
                  {'subjects': subjects, 'form': form, 'settings': settings, 'today': today,
                   'examination': examination,'start_date':start_date,'end_date':end_date})


def exam_delete(request, pk):
    if request.user.is_authenticated:
        user = request.user
    subject = get_object_or_404(Exam, pk=pk)
    subject.delete()
    return redirect('exams')


def plans(request):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    today=get_today(user)
    tomorrow=get_tomorrow(user)
    trips = []
    events = []
    plans = Plan.objects.filter(owner=user).order_by('start_date')
    if len(plans) == 0:
        empty = 1
    else:
        empty = 0
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    treshold = datetime.today().date() - timedelta(days=7)
    delete_plans = Plan.objects.filter(end_date__lt=treshold)
    for pl in delete_plans:
        pl.delete()
    return render(request, 'MSP/plans.html',
                  {'today': today, 'tomorrow': tomorrow, 'settings': settings, 'plans': plans,
                   'weekdays': weekdays_short, 'empty': empty,'start_date':start_date,'end_date':end_date})


def plan_edit(request, pk):
    if request.user.is_authenticated:
        user = request.user
    today=get_today(user)
    settings = Settings.objects.get(owner=user)
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.start_date = request.POST["start_date"]
            end_date = request.POST["end_date"]
            if end_date != '':
                plan.end_date = end_date
            else:
                plan.end_date = plan.start_date
            color = request.POST["color"]
            plan.color = color
            if plan.start_date:
                plan.start_date = datetime.strptime(plan.start_date, '%Y-%m-%d')
                plan.weekday = plan.start_date.weekday()
            plan.save()
            return redirect('plans')
    else:
        form = PlanForm(instance=plan)
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/plan_edit.html',
                  {'form': form, 'colors': colors, 'settings': settings, 'today': today, 'plan': plan, 'pk': pk,'start_date':start_date,'end_date':end_date})


def plan_new(request):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    today=get_today(user)
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.start_date = request.POST["start_date"]
            end_date = request.POST["end_date"]
            if end_date != '':
                plan.end_date = end_date
            else:
                plan.end_date = plan.start_date
            color = request.POST["color"]
            plan.color = color
            if plan.start_date:
                plan.start_date = datetime.strptime(plan.start_date, '%Y-%m-%d')
                plan.weekday = plan.start_date.weekday()
            plan.owner = user
            plan.save()
            return redirect('plans')
    else:
        form = PlanForm()
    start_date = Day.objects.get(date=settings.start_date,owner=user)
    end_date = Day.objects.get(date=settings.end_date,owner=user)
    return render(request, 'MSP/plan_edit.html', {'form': form, 'colors': colors, 'settings': settings, 'today': today,'start_date':start_date,'end_date':end_date})


def plan_delete(request, pk):
    if request.user.is_authenticated:
        user = request.user
    plan = get_object_or_404(Plan, pk=pk)
    plan.delete()
    return redirect('plans')


def timetable_week(request, pk):
    if request.user.is_authenticated:
        user = request.user
    days = Day.objects.filter(owner=user).order_by('date')
    settings = Settings.objects.get(owner=user)
    times = Time.objects.filter(owner=user)
    today=get_today(user)
    day = get_object_or_404(Day, pk=pk)
    week = Day.objects.filter(week=day.week, owner=user,date__gte=settings.start_date,date__lte=settings.end_date)
    monday = week[0]
    weeklength = len(week) - 1
    sunday = week[weeklength]
    week_pk = monday.pk
    weekspan = range(0, 7)
    lessons = Lesson.objects.filter(date__gte=monday.date, date__lte=sunday.date, owner=user).exclude(start_time=None)
    plans = Plan.objects.filter(start_date__gte=monday.date, start_date__lte=sunday.date, owner=user).exclude(
        start_time=None)
    exams = Exam.objects.filter(date__gte=monday.date, date__lte=sunday.date, owner=user).exclude(start_time=None)
    start_times = [lesson.start_time for lesson in lessons]
    start_times.extend([plan.start_time for plan in plans])
    start_times.extend([exam.start_time for exam in exams])
    end_times = [lesson.end_time for lesson in lessons]
    end_times.extend([plan.end_time for plan in plans])
    academic_hour = timedelta(minutes=settings.lesson_length)
    end_times.extend([(datetime.combine(date.today(), exam.start_time) + academic_hour).time() for exam in exams])
    hours = None
    if end_times != [] and start_times != []:
        min_time = int(datetime.combine(date.today(), time(hour=min(start_times).hour)).timestamp())
        if max(end_times).hour==23:
            max_time = int(datetime.combine(date.today(), time(hour=23)).timestamp())
        else:
            max_time = int(datetime.combine(date.today(), time(hour=max(end_times).hour + 1)).timestamp())
        hours = [[None]]
        for t in range(min_time, max_time, 3600):
            hours[-1].extend([datetime.fromtimestamp(t).time(), datetime.fromtimestamp(t + 3600).time()])
            hours.append([datetime.fromtimestamp(t).time()])
        hours[-1].extend([datetime.fromtimestamp(t + 3600).time(), None])
    time_delta = timedelta(hours=1)
    hometasks = Hometask.objects.filter(owner=user)
    exams = Exam.objects.filter(owner=user)
    blanks=[]
    for day in week:
        if len(Lesson.objects.filter(date=day.date)) == 0  and len(Exam.objects.filter(date=day.date)) == 0:
            blanks.append(day)
    return render(request, 'MSP/timetable_week.html',
                  {'pk': week_pk, 'settings': settings, 'today': today, 'times': times, 'monday': monday,
                   'sunday': sunday, 'week': week, 'weekspan': weekspan, 'weekdays': weekdays_short, 'lessons': lessons,
                   'exams': exams, 'plans': plans, 'hours': hours, 'time_delta': time_delta, 'hometasks': hometasks,
                   'exams': exams, 'days': days,'blanks':blanks})


def timetable_month(request, pk):
    if request.user.is_authenticated:
        user = request.user
    settings = Settings.objects.get(owner=user)
    times = Time.objects.filter(owner=user)
    today=get_today(user)
    day = get_object_or_404(Day, pk=pk)
    whole_month = Day.objects.filter(date__month=day.date.month, owner=user)
    month = whole_month[0].date.month
    month_meta = months[month - 1]
    month_pk = day.pk
    next = len(whole_month)
    previous = -len(Day.objects.filter(date__month=day.date.month - 1, owner=user))
    weekspan = range(0, 7)
    weekset = set([day.week for day in whole_month])
    weeks = [Day.objects.filter(week=week, owner=user) for week in weekset]
    lessons = Lesson.objects.filter(date__month__gte=month - 1, date__month__lte=month + 1, owner=user)
    exams = Exam.objects.filter(date__month__gte=month - 1, date__month__lte=month + 1, owner=user)
    plans = Plan.objects.filter(start_date__month__gte=month - 1, start_date__month__lte=month + 1, owner=user)
    days = Day.objects.filter(owner=user).order_by('date')
    return render(request, 'MSP/timetable_month.html',
                  {'pk': month_pk, 'settings': settings, 'today': today, 'times': times, 'month': month,
                   'month_meta': month_meta, 'next': next, 'previous': previous, 'weeks': weeks, 'weekspan': weekspan,
                   'lessons': lessons, 'exams': exams, 'plans': plans, 'days': days})


def feedback(request):
    if request.method=="POST":
        send_mail('Новый отзыв','Here is the message.','from@example.com',['thebadgirl1999@gmail.com'],fail_silently=False)
    return render(request, 'MSP/feedback.html',{})