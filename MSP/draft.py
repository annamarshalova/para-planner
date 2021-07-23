if first_lesson_start0 != settings.first_lesson_start or lesson_length0 != settings.lesson_length or break_length0 != settings.break_length or max_lessons0 < settings.max_lessons:
    Time.objects.all().delete()
    from_time = settings.first_lesson_start
    lesson_delta = timedelta(minutes=settings.lesson_length)
    break_delta = timedelta(minutes=settings.break_length)
    for i in range(settings.max_lessons):
        time = Time(number=i + 1)
        time.start_time = from_time
        time.end_time = (datetime.combine(date.today(), time.start_time) + lesson_delta).time()
        time.save()
        from_time = (datetime.combine(date.today(), time.end_time) + break_delta).time()
elif max_lessons0 > settings.max_lessons:
    for i in range(settings.max_lessons, max_lessons0):
        Time.objects.all()[i].delete()


<div id="edit_schedule" style="position:absolute;top:75px;left:800px;display:none;">
    <p style="position:absolute;font-size:40px;width:900px;font-size:40px;font-weight:bold;">Расписание звонков</p>
    <table style="position:absolute; top:100px;font-size:20px;">
    {% for time in schedule %}
        <tr>
      <td>{{ time.number }}</td>
      <td><input type="time"  name ='start_time{{time.number}}' value={{ time.start_time }}></td>
      <td><input type="time" name ='end_time{{time.number}}' value={{ time.end_time }}></td>
        </tr>
    {% endfor %}
        </table>
    <button type="submit" onclick="Show_schedule()" style="position:absolute;top:300px;" >Сохранить</button>
</div>

for time in schedule:
    schedule_form = TimeForm(request.POST, instance=time)
    if schedule_form.is_valid():
        time_form = schedule_form.save(commit=False)
        time_form.save()


{% block schedule %}
    <form method="POST" class="post-form" style="position:absolute; top:100px;font-size:20px;">{% csrf_token %}
        <table>

        {% for time_form in schedule_forms %}
        <tr>
        <td class="number"></td>
      <td>{{ time_form.start_time}}</td>
      <td>{{ time_form.end_time}}</td>
         </tr>
            {% endfor %}
            </table>
        <br>
        <br>
        <button type="submit" class="save btn btn-default">Сохранить</button>
    </form>
{% endblock %}
</div>

for time in schedule:
    time_form = TimeForm(request.POST, instance=time)
    if time_form.is_valid():
        time_form = time_form.save(commit=False)
        time_form.save()
    else:
        schedule_forms = []
        for time in schedule:
            schedule_forms.append(TimeForm(request.POST, instance=time))
        return render(request, 'MSP/schedule.html',
                      {'settings': settings, 'schedule': schedule, 'schedule_forms': schedule_forms})
return redirect('settings')
else:
schedule_forms = []
for time in Time.objects.all():
    schedule_forms.append(TimeForm(request.POST, instance=time))
return render(request, 'MSP/schedule.html',
              {'settings': settings, 'schedule': schedule, 'schedule_forms': schedule_forms})

function Stand(time){
if (time.length<5){
time='0'+time;}
return time;
}