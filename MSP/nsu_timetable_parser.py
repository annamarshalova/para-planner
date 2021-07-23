from icalendar import Calendar
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup
class Lesson:
    def __init__(self,title=None,type=None,start_time=None,end_time=None,weekday=None,classroom=None,teacher=None,weeks=None):
        self.title=title
        self.start_time=start_time
        self.start_time=start_time
        self.end_time=end_time
        self.weekday=weekday
        self.classroom=classroom
        self.type=type
        self.teacher=teacher
        self.weeks=weeks
subjects=[]
timetable=requests.post('https://table.nsu.ru/group/19812.2/').text
soup=BeautifulSoup(timetable,'html.parser')
table=soup.find(class_='time-table')
for row in table.find_all('tr'):
    try:
        columns = row.find_all('td')
        start_time = columns[0].string
        for i in range(1,len(columns)):
            if columns[i].find_all(class_='cell'):
                subject = Lesson()
                subject.start_time = start_time
                subject.weekday = i - 1
                subject.title = columns[i].find(class_='subject')['title']
                try:
                    subject.classroom = columns[i].find(class_='room').find('a').string
                except:
                    subject.classroom = columns[i].find(class_='room').string.strip(' \r')
                if columns[i].find(class_='tutor'):
                    subject.teacher = columns[i].find(class_='tutor').string
                subject.type = columns[i].find(class_=re.compile('type'))['title']
                weeks = columns[i].find(class_='week')
                print(weeks)
                if weeks:
                    week = weeks.string
                    if week == ' Нечетная':
                        subject.weeks = 1
                    if week == ' Четная':
                        subject.weeks = 2
                else:
                    subject.weeks = 12
                subjects.append(subject.__dict__)

    except:
        pass

print(subjects)
schedule=[]
times=soup.find_all('table')[0]
for row in times.find_all('tr'):
    schedule.append({})
    columns=row.find_all('td')
    schedule[-1].update({'time':columns[0].find('b').string[0]})
    start_end=str(columns[1]).split('<br/>')
    schedule[-1].update({'start':start_end})
#print(schedule)
