# -*- coding: utf-8 -*-

import bs4

hockey = u"""
<li class="supermain"><p>1-й период (2:2)</p></li>
<li class="match_review_left"><div><span class="number">01:58</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Кудако В. (Задержка клюшкой)</span></div></li>
<li class="match_review_left"><div><span class="number">06:33</span><span class="icon hockey-ball">&nbsp;</span><span class="name">Кодола В. Хабаров М. + Петунин А. </span></div></li>
<li class="match_review_right"><div><span class="number">07:40</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Удар клюшкой) Погоришный О.</span></div></li>
<li class="match_review_left"><div><span class="number">09:16</span><span class="icon hockey-ball">&nbsp;</span><span class="name">Морозов Е. Яковлев Е. + Кудако В. </span></div></li>
<li class="match_review_left"><div><span class="number">09:56</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Хохлов И. (Задержка клюшкой)</span></div></li>
<li class="match_review_right"><div><span class="number">11:17</span><span class="icon hockey-ball">&nbsp;</span><span class="name"> Эллис М. + Стремвалл М. Росен Р.</span></div></li>
<li class="match_review_right"><div><span class="number">15:06</span><span class="icon hockey-ball">&nbsp;</span><span class="name"> Лугин Д. + Коллинз Ш. Александров Ю.</span></div></li>
<li class="match_review_right"><div><span class="number">19:30</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Подножка) Архипов Д.</span></div></li>
<li class="supermain"><p>2-й период (1:0)</p></li>
<li class="match_review_right"><div><span class="number">01:21</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Задержка клюшкой) Макаренко П.</span></div></li>
<li class="match_review_left"><div><span class="number">08:23</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Макеев Н. (Подножка)</span></div></li>
<li class="match_review_left"><div><span class="number">12:20</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">Якимов Б. (Подножка)</span></div></li>
<li class="match_review_right"><div><span class="number">17:37</span><span class="icon block-time" title="Штраф на кол-во минут: 2">2</span><span class="name">(Подножка) Алтыбармакян А.</span></div></li>
<li class="match_review_left"><div><span class="number">17:52</span><span class="icon hockey-ball">&nbsp;</span><span class="name">Яковлев Е. Гераськин И. + Кудако В. </span></div></li>
"""

sli_hockey = """
<li class="match_review_left">
	<div>
		<span class="number">01:58</span>
		<span class="icon block-time" title="Штраф на кол-во минут: 2">2</span>
		<span class="name">Кудако В. (Задержка клюшкой)</span>	
	</div>	
</li>
"""

american_football = """
<li class="supermain"><p>1-я четверть (3:3)</p></li>
<li class="match_review_left"><div><span class="number">01:49</span><span class="name">Bailey D.</span></div></li>
<li class="match_review_right"><div><span class="number">13:00</span><span class="name">Crosby M.</span></div></li>
<li class="supermain"><p>2-я четверть (7:6)</p></li>
<li class="match_review_left"><div><span class="number">01:27</span><span class="name">Diggs S.</span></div></li>
<li class="match_review_left"><div><span class="number">01:27</span><span class="name">Bailey D.</span></div></li>
<li class="match_review_right"><div><span class="number">08:00</span><span class="name">Crosby M.</span></div></li>
<li class="match_review_right"><div><span class="number">14:59</span><span class="name">Crosby M.</span></div></li>
<li class="supermain"><p>3-я четверть (0:8)</p></li>
<li class="match_review_right"><div><span class="number">12:57</span><span class="name">Джонс А.</span></div></li>
<li class="match_review_right"><div><span class="number">12:57</span><span class="name">Allison G.</span></div></li>
<li class="supermain"><p>4-я четверть (0:6)</p></li>
<li class="match_review_right"><div><span class="number">09:09</span><span class="name">Джонс А.</span></div></li>
<li class="match_review_right"><div><span class="number">09:09</span><span class="name">Crosby M.</span></div></li>

"""

football = """
<li class="supermain"><p>1-й тайм (0:1)</p></li>
<li class="match_review_right"><div><span class="number">30'</span><span class="icon y-card">&nbsp;</span><span class="name">(Фол) Берн Д.</span></div></li>
<li class="match_review_left"><div><span class="number">36'</span><span class="icon y-card">&nbsp;</span><span class="name">Уинкс Г. (Подножка)</span></div></li>
<li class="match_review_right"><div><span class="number">37'</span><span class="icon goal">&nbsp;</span><span class="name"> (Гросс П.) Webster A.</span></div></li>
<li class="match_review_left"><div><span class="number">39'</span><span class="icon y-card">&nbsp;</span><span class="name">Санчес Д. (Задержка)</span></div></li>
<li class="match_review_right"><div><span class="number">42'</span><span class="icon y-card">&nbsp;</span><span class="name">(Задержка) Гросс П.</span></div></li>
<li class="supermain"><p>2-й тайм (2:0)</p></li>
<li class="match_review_left"><div><span class="number">53'</span><span class="icon goal">&nbsp;</span><span class="name">Кейн Х.</span></div></li>
<li class="match_review_left"><div><span class="number">56'</span><span class="name">Ло Селсо Дж.</span><span class="icon up">&nbsp;</span><span class="name"> Сессеньон Р.</span><span class="icon down">&nbsp;</span></div></li>
<li class="match_review_right"><div><span class="number">68'</span><span class="name">Мопей Н.</span><span class="icon up">&nbsp;</span><span class="name">Конноли А. </span><span class="icon down">&nbsp;</span></div></li>
<li class="match_review_left"><div><span class="number">68'</span><span class="name">Эриксен К.</span><span class="icon up">&nbsp;</span><span class="name"> Уинкс Г.</span><span class="icon down">&nbsp;</span></div></li>
<li class="match_review_left"><div><span class="number">72'</span><span class="icon goal">&nbsp;</span><span class="name">Алли Д. (Орье С.) </span></div></li>
<li class="match_review_left"><div><span class="number">74'</span><span class="icon y-card">&nbsp;</span><span class="name">Лукас (Грубая игра)</span></div></li>
<li class="match_review_left"><div><span class="number">76'</span><span class="name">Дайер Э.</span><span class="icon up">&nbsp;</span><span class="name"> Лукас</span><span class="icon down">&nbsp;</span></div></li>
<li class="match_review_right"><div><span class="number">76'</span><span class="name">Троссард Л.</span><span class="icon up">&nbsp;</span><span class="name">Бернардо </span><span class="icon down">&nbsp;</span></div></li>
<li class="match_review_right"><div><span class="number">83'</span><span class="name">Биссума И.</span><span class="icon up">&nbsp;</span><span class="name">Скелотто Э. </span><span class="icon down">&nbsp;</span></div></li>
<li class="match_review_left"><div><span class="number">84'</span><span class="icon y-card">&nbsp;</span><span class="name">Сиссоко М. (Фол)</span></div></li>
"""

"""
<li class="match_review_right">
    <div>
        <span class="number">30'</span>
        <span class="icon y-card">&nbsp;</span>
        <span class="name">(Фол) Берн Д.</span>
    </div>
</li>
<li class="match_review_left">
    <div>
        <span class="number">56'</span>
        <span class="name">Ло Селсо Дж.</span>
        <span class="icon up">&nbsp;</span>
        <span class="name"> Сессеньон Р.</span>
        <span class="icon down">&nbsp;</span>
    </div>
</li>
"""

# #print reviews.encode('utf-8')
home = u'ХК Нефтехимикааааа'
guest = u'ХК Ак Барс'

# print len(home)
# # print len(home.encode('utf-8'))

# print len(guest)
# # print len(guest.encode('utf-8'))

# OBREZ = 20


def fu(txt, column_width):
    txt = txt.strip()
    result = u'{1:<{0:}}|'.format(
        column_width, txt[:column_width] if len(txt) > column_width else txt)
    #print result.encode('utf-8')
    print len(result.encode('utf-8'))
    return result


# def f(txt, column_width):
#     txt = txt.encode('utf-8')
#     txt = txt.strip()
#     result = '{1:<{0:}}|'.format(
#         column_width, txt[:column_width] if len(txt) > column_width else txt)
#     print result
#     print len(result)
#     return result


# print len(home.encode('utf-8'))
# print len(guest.encode('utf-8'))

print len(home)
print len(guest)

lh = len(home)
lg = len(guest)

column_width_home = lh if lh >= lg else 2*lg - lh + 1
column_width_guest = lg if lg >= lh else 2*lh - lg + 1

print fu(home, column_width_home).encode('utf-8')
print fu(guest, column_width_guest).encode('utf-8')

# print f(home, 30)
# print f(guest, 30)

# links = []

# tag_reviews = bs4.BeautifulSoup(hockey, 'html.parser')

# lis = tag_reviews.findAll('li')

# for li in tag_reviews.findAll('li'):
#     class_ = li['class'][0]
#     #print class_
#     if class_ == u'supermain':
#         #print li.text
#         links.append(li.text)
#     else:
#         if class_ == 'match_review_left':            
#             link = u'{:<20}'.format(home)
#         else:
#             link = u'{:<20}'.format(guest)
#         div = li.find('div')
#         spans = div.findAll('span')
#         up_down = u''
#         name = u''
#         number = u''
#         icon = u''
#         for s in spans:            
#             #print s['class']
#             if len(s['class']) == 2:
#                 if s['class'][0] == u'icon':
#                     if s['class'][1] == u'block-time':
#              #           print s['title']
#                         icon = s['title']
#                     elif s['class'][1].find('ball') != -1 or s['class'][1] == 'goal':
#                         icon = u'ГОЛ!'
#                     elif s['class'][1] == u'y-card':
#                         icon = u'Желтая карточка'
#                     elif s['class'][1] == u'up':
#                         up_down = name + u'(вышел)'
#                         name = u''
#                     elif s['class'][1] == u'down':
#                         icon = up_down + name + u'(ушел)'
#                         up_down = u''
#                         name = u''            
#             else:
#                 if s['class'][0] == u'name':
#                     name = s.text
#                 elif s['class'][0] == u'number':
#                     number = s.text
#         link = link + u' |  ' + number + u' | ' + icon + u' | ' + name
#         print link.encode('utf-8')
#         links.append(link)


#print tag_reviews


