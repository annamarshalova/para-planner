from icalendar import Calendar
from datetime import datetime
import re
import json
import requests
from bs4 import BeautifulSoup

page=requests.post('https://www.unipage.net/ru/universities/best/russia').text
soup=BeautifulSoup(page,'html.parser')
table=soup.find(class_='t t-b')
names=[]
print(table)
a=table.find_all('a')
print(a)
for name in a:
    names.append(name.string)
print(names)
with open ('universities.json','w',encoding='utf-8') as js:
    json.dump(names,js,ensure_ascii=False)