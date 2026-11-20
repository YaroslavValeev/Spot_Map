import json
import time
import urllib.parse
import urllib.request

queries = [
    "Яхт-клуб Мегаспорт Мытищи",
    "коттеджный посёлок Любляна Семёновская Егорьевск",
    "село Федоскино Мытищи",
    "пейнтбольный клуб Гвардия Правдинский",
    "деревня Горчухино Наро-Фоминск",
    "ГРК Малибу Сорокино Мытищи",
    "Инженерный пруд Дмитров",
    "деревня Лопотово Солнечногорск",
    "Павленское озеро Серпухов",
    "Большой Путяевский пруд Сокольники",
    "Остров Мечты Андропова 1",
    "Исаковского 37к1с1 Москва",
    "Голиково Шоссейная 4",
    "река Москва СберСити Рублёво-Архангельское",
    "Борисовские пруды Наташинская",
]
for q in queries:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "countrycodes": "ru"}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "SpotMapOSINT/1.0 (local research)"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=25).read())
        if data:
            print(f"{q} -> {data[0]['lat']}, {data[0]['lon']} | {data[0].get('display_name','')[:90]}")
        else:
            print(f"{q} -> NONE")
    except Exception as e:
        print(f"{q} -> ERR {e}")
    time.sleep(1.1)
