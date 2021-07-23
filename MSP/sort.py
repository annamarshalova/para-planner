import json
with open('universities.json', 'r', encoding='utf-8') as js:
    universities = json.load(js)
universities.sort()
print(universities)
with open('universities.json', 'w', encoding='utf-8') as js:
    json.dump(universities,js,ensure_ascii=False)