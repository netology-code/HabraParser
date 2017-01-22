#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
import html
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from collections import Counter
from pandas import DataFrame
import numpy as np
import operator
import csv
import random
import time

months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
def StrToDate(strdate):
    parts = list(filter(None, (strdate).split(' ')))
    for i in range(0, len(parts), 1):
        if parts[0] == 'сегодня':
            publishdate = datetime.today().date()
        elif parts[0] == 'вчера':
            publishdate = (datetime.now() - timedelta(days=1)).date()
        else:
            formatter_string = "%d-%m-%y"
            datestring = parts[0] + '-' + str(months.index(parts[1]) + 1)
            if parts[2] == 'в':
                datestring = datestring + '-' + str(datetime.today().year)
            else:
                datestring = datestring + '-' + parts[2]
            publishdate = datetime.strptime(datestring, '%d-%m-%Y').date()
    return publishdate

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



url_real = response.geturl()
htmlinfo = response.info()
html = response.read()

#собираем все страницы - результаты поиска и складываем их url'ы в переменную urls
#учитываем, что выводятся не все результаты поиска, поэтому сначала нужно выяснить номер последней страницы
soup = BeautifulSoup(html)
html_lastpage = soup.find('ul', attrs={'id':'nav-pages'}).find('a', attrs={'title':'Последняя страница'}).get('href')
start = html_lastpage.find('page') + len('page')
end = len(html_lastpage)
lastpage = int(html_lastpage[start:end-1])


#первый фильтр: берем все статьи с лейблом tutorial (Обучающий материал)
#и для них сразу получаем максимум информации, которая сейчас доступна: дата публикации, название, ссылка, хабы и пр.
page = 0
tutorials = []
#tutorial: { date, title, url, {hubs}, views, favoritecount, commentscount, author }
random.seed()
while page < lastpage:
#while page < 12:
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
            time.sleep(1)
            #tagsarr = BeautifulSoup(urllib.request.urlopen(articleurl).read()).find_all('a', attrs={'rel': 'tag'})
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

#считаем статистику: распределение обучающих материалов по годам, топ-20 статей по: добавлению в избранное,
#самые обсуждаемые (по количеству комментариев), самый пишущий автор
dates = []
mostfavored = []
mostcommented = []
authors = []
id = 0
for tutorial in tutorials:
    dates.append(tutorial[0].year) #распределение по годам
    mostfavored.append([id, tutorial[5]])
    mostcommented.append([id, tutorial[6]])
    authors.append(tutorial[7])
    id+= 1

def customsort(i):
    return i[1]

stats = Counter(dates).items()
mostfavored.sort(key=lambda i: i[1], reverse= True)
mostcommented.sort(key=customsort, reverse = True)
statsauthors = Counter(authors).most_common()

#[(l,k) for k,l in sorted([(j,i) for i,j in statsauthors.items()], reverse=True)]


#строим визуализации: распределение статей по годам, рейтинг самых пишущих авторов
#plt.interactive(False)
plt.rc('font', family='Arial')

figure = plt.figure(1)
#pltcounts = plt.subplot(121)
plt.title('Распределение статей по годам')
x = []
y = []
for stat in stats:
    x.append(stat[0])
    y.append(stat[1])
plt.plot(x, y)
plt.interactive(False)
plt.show(block=True)

#pltauthors = plt.subplot(122)

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

#add the numbers to the side of each bar
for p, c, ch in zip(pos, x, y):
    plt.annotate(str(ch), xy=(ch + 1, p + .5), va='center')

#cutomize ticks
ticks = plt.yticks(pos + .5, x)
xt = plt.xticks()[0]
plt.xticks(xt, [' '] * len(xt))
plt.grid(axis = 'x', color ='white', linestyle='-')

#set plot limits
plt.ylim(pos.max(), pos.min() - 1)
plt.xlim(0, 30)
#plt.interactive(False)
plt.show(block=True)

print("Мы сделали это!")
