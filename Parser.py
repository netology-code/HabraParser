import urllib.request
from bs4 import BeautifulSoup
#import pandas as pd
import html
from datetime import datetime, date, time, timedelta
import matplotlib.pyplot as plt
from collections import Counter

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

#получаем результаты поиска
#response = urllib.request.urlopen('https://habrahabr.ru/search/?target_type=posts&q=python&order_by=date')
#html = response.read()

#определяем количество страниц

#генерируем запрос на выдачу страницы
#values = {'q' : 'python',
#    'target_type' : 'posts',
#    'order_by' : 'date' }
#url_withparams = urllib.parse.urlencode(values)
#url_full = "https://habrahabr.ru/search/?" + url_withparams
url_full = "https://habrahabr.ru/hub/python/all"
try: response = urllib.request.urlopen(url_full)
except urllib.error.URLError as e:
    print('Ошибка при открытии страницы: ', e.reason)
#сразу идем на хаб python


url_real = response.geturl()
htmlinfo = response.info()
html = response.read()

#собираем все страницы - результаты поиска и складываем их url'ы в переменную urls
#учитываем, что выводятся не все результаты поиска, поэтому сначала нужно выяснить номер последней страницы
soup = BeautifulSoup(html)
#html_pages = soup.find('ul', attrs={'id':'nav-pages'})
html_lastpage = soup.find('ul', attrs={'id':'nav-pages'}).find('a', attrs={'title':'Последняя страница'}).get('href')
start = html_lastpage.find('page') + len('page')
end = len(html_lastpage)
lastpage = int(html_lastpage[start:end-1])
'''
lis = [li for li in html_pages.findAll('li')]
urls = []
for li in lis:
    try:
        url = "https://habrahabr.ru" + li.find('a', href=True).get('href')
        try:
            urllib.request.urlopen(url)
            urls.append(url)
        except:
            print('Страницы закончились')

    except :
        print('Первая страница')
        urls.append(url_full)
'''

#первый фильтр: берем все статьи с лейблом tutorial (Обучающий материал)
#и для них сразу получаем максимум информации, которая сейчас доступна: дата публикации, название, ссылка, хабы
page = 0
tutorials = []
#tutorial: { date, title, url, {hubs}, views, favoritecount, commentscount, author }
#while page < lastpage:
while page < 12:
    page = page + 1
    url = 'https://habrahabr.ru/hub/python/page' + str(page) + '/'
    matches = BeautifulSoup(urllib.request.urlopen(url).read()).find_all('span', attrs={'class': 'flag_tutorial', 'title': 'Обучающий материал'})
    for match in matches:
        tutorial = []
        article = match.find_parent('div', attrs={'class': 'post_teaser'})
        #tutorial.append(article.find('span', attrs={'class': 'post__time_published'}).text)
        datestr = article.find('span', attrs={'class': 'post__time_published'}).text.replace('\n','')
        tutorial.append(StrToDate(datestr))
        tutorial.append(article.find('a', attrs={'class': 'post__title_link'}).text)
        tutorial.append(article.find('a', attrs={'class': 'post__title_link'}).get('href'))
        names = article.find_all('a', attrs={'class': 'hub'})
        hubs = []
        for name in names:
            hubs.append(name.text)
        tutorial.append(hubs)
        views = article.find('div', attrs={'class': 'views-count_post'}).text
        tutorial.append(ViewsToNumber(views))
        try:
            tutorial.append(int(article.find('span', attrs={'class': 'favorite-wjt__counter'}).text))
        except:
            tutorial.append(int(0))
        try:
            tutorial.append(int(article.find('a', attrs={'class': 'post-comments__link'}).text))
        except:
            tutorial.append(int(0))
        author = article.find('a', attrs={'class': 'post-author__link'}).text.replace('\n','')
        author = author.replace(' ', '')
        tutorial.append(author)
        tutorials.append(tutorial)
        print(tutorial)

#считаем статистику: распределение обучающих материалов по годам, топ-20 статей по: добавлению в избранное,
#по лайкам, самые обсуждаемые (по количеству комментариев), самый пишущий автор
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
statsauthors = Counter(authors).items()




figure = plt.figure(1)
pltcounts = plt.subplot(211)
plt.title('Распределение статей по годам')
x = []
y = []
for stat in stats:
    x.append(stat[0])
    y.append(stat[1])
plt.plot(x, y)
pltfavored = plt.subplot(212)
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
#plt.plot(x,y)
plt.show()

