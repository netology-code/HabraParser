#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import Counter
from pandas import DataFrame
import numpy as np
import csv

#фунцкция-парсер даты с Хабра
months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
def StrToDate(strdate):
    parts = list(filter(None, (strdate).split(' ')))
    for i in range(0, len(parts), 1):
        if parts[0] == 'сегодня':
            publishdate = datetime.today().date()
        elif parts[0] == 'вчера':
            publishdate = (datetime.now() - timedelta(days=1)).date()
        else:
            datestring = parts[0] + '-' + str(months.index(parts[1]) + 1)
            if parts[2] == 'в':
                datestring = datestring + '-' + str(datetime.today().year)
            else:
                datestring = datestring + '-' + parts[2]
            publishdate = datetime.strptime(datestring, '%d-%m-%Y').date()
    return publishdate

#функция, преобразующая текстовое представление числа (1,4k) в число
def ViewsToNumber(strvcount):
    coeff = 1
    coeff2 = 1
    if (strvcount[len(strvcount)-1] == 'k'):
        coeff = 1000
        coeff2 = 100
        strvcount = strvcount[0:len(strvcount)-1]
    elif (strvcount[len(strvcount)-1] == 'm'):
        coeff = 1000000
        coeff2 = 1000
        strvcount = strvcount[0:len(strvcount)-1]
    parts = strvcount.split(',')
    try:
        count = int(parts[0])*coeff
        if len(parts) > 1:
            count = count + int(parts[1]) * coeff2
    except:
        count = 0

    return count

#генерируем запрос на выдачу страницы
#values = {'q' : 'python',
#    'target_type' : 'posts',
#    'order_by' : 'date' }
#url_withparams = urllib.parse.urlencode(values)
#url_full = "https://habrahabr.ru/search/?" + url_withparams
#сразу идем на хаб Хабра про Python
url_full = "https://habrahabr.ru/hub/python/all"
try: response = urllib.request.urlopen(url_full)
except urllib.error.URLError as e:
    print('Ошибка при открытии страницы: ', e.reason)

url_real = response.geturl() # вот так можно проверить "правильную" ссылку - в случае, если есть перенаправление
html = response.read()

#учитываем, что результаты поиска выводятся постранично, поэтому сначала нужно выяснить номер последней страницы
soup = BeautifulSoup(html)
html_lastpage = soup.find('ul', attrs={'id':'nav-pages'}).find('a', attrs={'title':'Последняя страница'}).get('href')
start = html_lastpage.find('page') + len('page')
end = len(html_lastpage)
lastpage = int(html_lastpage[start:end-1])


#берем все статьи с лейблом tutorial (Обучающий материал)
#и для них сразу получаем максимум информации, которая сейчас доступна: дата публикации, название, ссылка, хабы и пр.
page = 0
tutorials = []
#tutorial: { date, title, url, {hubs}, views, favoritecount, commentscount, author, {tags} }
#while page < lastpage:
while page < 1:
    page = page + 1
    url = 'https://habrahabr.ru/hub/python/page' + str(page) + '/'
    matches = BeautifulSoup(urllib.request.urlopen(url).read()).find_all('span', attrs={'class': 'flag_tutorial', 'title': 'Обучающий материал'})
    for match in matches:
        #запись с информацией про статью
        tutorial = []
        #ищем весь блок html про статью
        article = match.find_parent('div', attrs={'class': 'post_teaser'})
        #дата публикации статьи. преобразуется в объект Date нашей функцией StrToDate()
        datestr = article.find('span', attrs={'class': 'post__time_published'}).text.replace('\n','')
        tutorial.append(StrToDate(datestr))
        #ссылка на страницу статьи
        tutorial.append(article.find('a', attrs={'class': 'post__title_link'}).text)
        articleurl = article.find('a', attrs={'class': 'post__title_link'}).get('href')
        tutorial.append(articleurl)
        #хабы, к которым относится статья
        names = article.find_all('a', attrs={'class': 'hub'})
        hubs = []
        for name in names:
            hubs.append(name.text)
        tutorial.append(hubs)
        #количество просмотров. выглядит как 1,4k, поэтому преобразуем в число нашей функцией ViewsToNumber()
        views = article.find('div', attrs={'class': 'views-count_post'}).text
        tutorial.append(ViewsToNumber(views))
        #количество добавлений статьи в избранное. может не быть значения, поэтому ловим ошибку
        try:
            tutorial.append(int(article.find('span', attrs={'class': 'favorite-wjt__counter'}).text))
        except:
            tutorial.append(int(0))
        #количество комментариев к статье. может не быть значения, поэтому ловим ошибку
        try:
            tutorial.append(int(article.find('a', attrs={'class': 'post-comments__link'}).text))
        except:
            tutorial.append(int(0))
        #автор статьи. убираем лишние переводы строк и пробелы
        author = article.find('a', attrs={'class': 'post-author__link'}).text.replace('\n','')
        author = author.replace(' ', '')
        tutorial.append(author)
        # необходимо сходить по ссылке на страницу статьи и забрать теги
        #time.sleep(random.randint(0, 2))
        tags = []
        try:
            tagsarr = BeautifulSoup(urllib.request.urlopen(articleurl).read()).find_all('a', attrs={'rel': 'tag'})
            for tag in tagsarr:
                tags.append(tag.text)
        except:
            pass
        tutorial.append(tags)
        #сохраняем очередную запись о статье в массив статей
        tutorials.append(tutorial)
        print(tutorial)

#записываем список статей в CSV-файл, чтобы каждый раз его не качать заново
#для того, чтобы файл корректно открывался в Excel как таблица,
#необходимо поменять разделители на ; и задать кодировку Windows 1251 (Excel не понимает utf-8)
csv.register_dialect('customcsv', delimiter=';', quoting=csv.QUOTE_NONE, quotechar='',escapechar='\\')
with open("output.csv", "w", encoding='cp1251', newline='') as f:
    writer = csv.writer(f, 'customcsv')
    writer.writerows(tutorials)

#загружаем всю информацию о 222 статьях из CSV-файла
tutorials = []
with open('все туториалы по питону с 2009 года.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=';')
    for row in readCSV:
        # tutorial: { date, title, url, {hubs}, views, favoritecount, commentscount, author, {tags} }
        tutorial = []
        tutorial.append(datetime.strptime(row[0], '%Y-%m-%d').date())
        tutorial.append(row[1])
        tutorial.append(row[2])
        hubs = list(str(row[3]).replace('[', '').replace(']', '').replace('\'', '').split(','))
        tutorial.append(hubs)
        tutorial.append(row[4])
        tutorial.append(row[5])
        tutorial.append(row[6])
        tutorial.append(row[7])
        tags = list(str(row[8]).replace('[', '').replace(']', '').replace('\'', '').split(','))
        tutorial.append(tags)

        tutorials.append(tutorial)


#считаем статистику: распределение обучающих материалов по годам, топ-20 статей по: добавлению в избранное,
#самые обсуждаемые (по количеству комментариев), самый пишущий автор
dates = []
mostfavored = []
mostcommented = []
authors = []

for tutorial in tutorials:
    dates.append(tutorial[0].year) #распределение по годам
    mostfavored.append([tutorial[1], tutorial[5]])
    mostcommented.append([tutorial[1], tutorial[6]])
    authors.append(tutorial[7])

# пример двух вариантов сортировки: либо объявляем и передаем функцию, либо используем lambda-выражение
def customsort(i):
    return i[1]

dictstats = Counter(dates).items()
stats = []
for ds in dictstats:
    stats.append(ds)
stats.sort()
mostfavored.sort(key=lambda i: i[1], reverse= True)
mostcommented.sort(key=customsort, reverse = True)
statsauthors = Counter(authors).most_common()

#строим визуализацию по распределению статей по годам
plt.rc('font', family='Arial') #задаем шрифт явно, иначе кириллица не отображается

figure = plt.figure(1)
plt.title('Распределение статей по годам')

x = []
y = []
for stat in stats:
    x.append(int(stat[0]))
    y.append(stat[1])
plt.xkcd()
plt.plot(x, y)
plt.interactive(False)
plt.xticks(x, x)
plt.show(block=True)

#строим визуализацию по самым пишущим авторам
figure = plt.figure(2)
plt.title('Самые пишущие авторы')
x = []
y = []
count = 0
for stat in statsauthors:
    count += 1
    x.append(stat[0])
    y.append(stat[1])
    if count >= 20:
        break

grad = DataFrame({'publications' : y, 'author': x})
pos = np.arange(len(y))
plt.title('Топ-20 самых пишущих авторов')
plt.barh(pos, y)

#записываем количество статей справа от полосы
for p, c, ch in zip(pos, x, y):
    plt.annotate(str(ch), xy=(ch + 1, p + .5), va='center')

#настраиваем область диаграммы
ticks = plt.yticks(pos + .5, x)
xt = plt.xticks()[0]
plt.xticks(xt, [' '] * len(xt))
plt.grid(axis = 'x', color ='white', linestyle='-')
plt.ylim(pos.max(), pos.min() - 1)
plt.xlim(0, 30)
plt.show(block=True)

#выводим топ-20 статей по добавлению в избранное
id = 0
print('\n***Топ-20 статей по добавлению в избранное***')
for fav in mostfavored:
    id+= 1
    print(str(id) + '. ' + fav[0] + ' (' + str(fav[1]) + ')')
    if id == 20:
        break

#выводим топ-20 статей по добавлению в избранное
id = 0
print('\n***Топ-20 комментируемых статей***')
for comm in mostcommented:
    id+= 1
    print(str(id) + '. ' + comm[0] + ' (' + str(comm[1]) + ')')
    if id == 20:
        break

#насколько совпадают самые добавляемые и самые комментируемые?
id = 0
favs = set()
for fav in mostfavored:
    id+= 1
    favs.add(fav[0])
    if id == 20:
        break

id = 0
comms = set()
for com in mostcommented:
    id+= 1
    comms.add(com[0])
    if id == 20:
        break

result = set(favs) & set(comms)

print('\n***Самые популрные статьи***')
id = 0
for res in result:
    id+= 1
    print (str(id) + '. ' + res)
    id += 1

print("Мы сделали это!")
