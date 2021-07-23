from icalendar import Calendar
from datetime import datetime
import re
class Lesson:
    def __init__(self,title=None,type=None,start_time=None,end_time=None,weekday=None,classroom=None,teacher=None):
        self.title=title
        self.start_time=start_time
        self.start_time=start_time
        self.end_time=end_time
        self.weekday=weekday
        self.classroom=classroom
        self.type=type
        self.teacher=teacher
subjects=[]
g = open('static/calendars/19812_2.ics','r',encoding='utf-8')
gcal = Calendar.from_ical(g.read())
for component in gcal.walk():
    if component.name=='VEVENT':
        subject=Lesson()
        fullname=str(component.get('summary'))
        subject.type=str(re.findall('(\(.*?\))',fullname)[-1].strip('()'))
        subject.title=fullname.replace(f'({subject.type})','').rstrip(' ')
        subject.start_time=component.decoded('dtstart').astimezone().strftime("%H:%M")
        subject.end_time = component.decoded('dtend').astimezone().strftime("%H:%M")
        subject.weekday= component.decoded('dtstart').weekday()
        subject.teacher = str(component.get('description')).replace('Преподаватель: ','')
        try:
            subject.classroom = re.findall('[а-я]?\d+[а-я]?',str(component.get('location')))[0]
        except:
            subject.classroom=str(component.get('location'))
        subjects.append(subject)
g.close()


for subject in subjects:
    print(subject.__dict__)